import pandas as pd
import numpy as np
from os import chdir
from os import get_terminal_size
from shutil import move, copy
from pathlib import Path
import json
import subprocess
from pprint import pprint
from fuzzywuzzy import fuzz, process

from mylogger import get_filelog

from finance.init_scripts import get_dirs, DB_NAMES


def load_new(main_dir=Path('.'),
             return_dbs=False,
             write_out_dbs=True,
             move_new_txs=True,
             write_out_path=None):
    """
    Main sequence for loading new txs.
    I think everything else either testing or obsolete.
    Sequence broken into functions, not for reuse but to aid
    structural transparency.
    """

    main_dir = Path(main_dir).absolute()

    # load the dbs (a dict of dfs)
    dbs = load_dbs(main_dir)

    for acc_path in (main_dir / 'tx_accounts').iterdir():
        print('entering', acc_path.name)

        prepare_new_csv_files(acc_path.absolute())

        tx_dirs = get_dirs(acc_path)

        for dir in tx_dirs:
            print(("- " + dir).ljust(20), str(len(tx_dirs[dir])).rjust(3))

        if tx_dirs['new_csvs']:

            df = load_new_csv_files(tx_dirs['new_csvs'], acc_path)
            df = trim_df(df, acc_path, dbs['tx_db'],
                         write_out_dbs=write_out_dbs,
                         write_out_path=write_out_path)
            df = add_target_acc_col(df, acc_path, dbs)

            # check for discontinuity only if account reports balance
            # df_check = check_df(df, acc_path)

            # update the dbs
            dbs['fuzzy_db']    = update_fuzzy_db(df, dbs['fuzzy_db'])
            dbs['unknowns_db'] = update_unknowns_db(df, dbs['unknowns_db'])
            dbs['tx_db']       = update_tx_db(df, dbs['tx_db'])

            # move the processed tx files to another folder
            if move_new_txs:
                for f in tx_dirs['new_csvs']:
                    move(f, acc_path / 'processed_csvs' / f.name)
        else:
            print('did not find tx_dirs["new_csvs"]')

    # save dbs to disc
    if write_out_dbs:
        if write_out_path is None:
            out_dir = main_dir
        else:
            out_dir = Path(write_out_path)

        for db in dbs:
            dbs[db].to_csv(out_dir / (db + '.csv'))

        print('archiving')
        archive_dbs(acc_path=main_dir)

    if return_dbs:
        return(dbs)


def load_new_csv_files(new_txs_files, acc_path):
    dfs = []
    for new_txs_file in new_txs_files:
        new_txs_df = pd.read_csv(new_txs_file)
        new_txs_df['source'] = new_txs_file.name
        dfs.append(new_txs_df)
    df = pd.concat(dfs)
    with open(acc_path / 'parser.json', 'r') as fp:
        parser = json.load(fp)
    df = format_new_txs(df, account_name=acc_path.name, parser=parser)
    df['ts'] = pd.Timestamp(pd.datetime.now())
    return df.sort_values(['date', 'ITEM'])


def trim_df(df, acc_path, tx_db,
            write_out_dbs=True, write_out_path=None):
    """
    For an input df, drop any transactions that have previously been loaded
    for this account.
    """

    prev_txs = tx_db.loc[tx_db['accX'] == acc_path.name].reset_index()

    if len(prev_txs) == 0:
        return df

    df = df.reset_index()

    # make sure only comparing the same columns
    common_cols = list(set(prev_txs.columns)
                       .intersection(df.columns))
    prev_txs = prev_txs[common_cols]
    df = df[common_cols]

    last_tx_of_prev = tuple(prev_txs.iloc[-1].copy())

    # work out if there is an overlap, and trim if so
    match_index = -1
    df_tuples = [tuple(y) for y in df.values]
    for i, x in enumerate(df_tuples):
        if x == last_tx_of_prev:
            match_index = i
    if match_index != -1:
        trimmed_df = df.iloc[(match_index + 1):].copy()
    else:
        trimmed_df = df.copy()

    if write_out_dbs:

        if write_out_path is None:
            out_dir = acc_path
        else:
            out_dir = write_out_path / acc_path

        out_path = out_dir / 'prev_txs.csv'
        with open(acc_path / 'parser.json', 'r') as fp:
            parser = json.load(fp)

        trimmed_df.to_csv(out_path, mode='a', header=False,
                                    date_format=parser['date_format'])
    return trimmed_df



def add_target_acc_col(df, acc_path, dbs):
    """
    Get target account assignments (categories)
    """
    accYs = assign_targets(df._item, acc_path.name,
                                unknowns_db=dbs['unknowns_db'],
                                fuzzy_db=dbs['fuzzy_db'],
                                cat_db=dbs['cat_db'],
                               )

    # make a df with accY, accY and mode columns
    df['accX'] = acc_path.name
    df['accY'] = [x[0] for x in accYs]
    df['mode'] = [x[1] for x in accYs]

    return df


def update_fuzzy_db(df, fuzzy_db):
    """
    Get any fuzzy matches and append to fuzzy_db
    """

    new_fuzzies = (df.loc[df['mode'] == 'new fuzzy']
                     .set_index('_item', drop=True))
    new_fuzzies['status'] = 'unconfirmed'
    new_fuzzies = new_fuzzies[fuzzy_db.columns]

    return tidy(fuzzy_db.append(new_fuzzies))


def update_unknowns_db(df, unknowns_db):
    """
    Get any new unknowns and append to unknowns_db
    """
    new_unknowns = (df.loc[df['mode'] == 'new unknown']
                     .set_index('_item', drop=True))
    unknowns_db = unknowns_db.append(new_unknowns[unknowns_db.columns])

    return tidy(unknowns_db)


def update_tx_db(df, tx_db):
    """
    Assign ids to the new txs and append to tx_db
    """
    max_current = int(tx_db['id'].max()) if len(tx_db>0) else 100

    df['id'] = np.arange(max_current + 1,
                         max_current + 1 + len(df)).astype(int)

    return tx_db.append(df[tx_db.columns])


def check_df(df, acc_path):
    """
    TODO
    Check for balance continuity ONLY for accounts with balance.
    Pass the tx_db and take the last balance for the account.
    Use this to check for continuity across the gap, and within the
    new txs.
    """

    if balance_continuum(df).sum():
        print('WARNING:', acc_path.name, 'has a balance discontinuity')
        print(balance_continuum(df))
        return 1

    if df.duplicated().values.sum():
        print('WARNING:', acc_path.namec, 'has duplicated values')
        return 1

    return 0


def load_dbs(dir_path=Path()):
    """
    Loads dbs from disk, returning a dict
    """

    dbs = {}

    for db in DB_NAMES:
        dbs[db] = pd.read_csv(dir_path / (db + '.csv'),
                              index_col='date' if db == 'tx_db' else '_item')

    dbs['tx_db'].index = pd.to_datetime(dbs['tx_db'].index)

    return dbs


def prepare_new_csv_files(dir_path):
    prep_script_path = dir_path.absolute() / 'prep.py'
    if prep_script_path.exists():
        subprocess.run(['python', str(prep_script_path.absolute()),
                        str(dir_path)])
    else:
        print('cannot find', prep_script_path)


def archive_dbs(acc_path=None, annotation=None, archive_path=None):
    """
    Save a snapshot of the 4 dbs
    """

    print('\nPassed values:')
    print('Archive path', archive_path)
    print('acc_path', acc_path)

    if acc_path is None:
        acc_path = Path()

    proj_name = acc_path.name

    if archive_path is None:
        print('\nIn assigning archive_path')
        archive_path = acc_path / 'db_archive'
        print('Archive path', archive_path.absolute())

    if not Path(archive_path).exists():
        Path(archive_path).mkdir()

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M")


    print('\nBefore archiving')
    print('Archive path', archive_path.absolute())
    print('acc_path', acc_path.absolute())

    if annotation is None:
        annotation = ""
    else:
        annotation = "_" + annotation

    for db in DB_NAMES:

        dir_out = archive_path / db
        if not Path(dir_out).exists():
            Path(dir_out).mkdir()

        print('archiving to', dir_out.absolute())
        copy(str(acc_path / (db + '.csv')), 
             str(dir_out / (ts + annotation + '.csv') ))


def format_new_txs(new_tx_df, account_name, parser):

    """Return a tx_df in standard format, with date index,
    and columns: 'date', 'ITEM', '_item', 'net_amt', 'balance', 'source'

    new_tx_df    : a df with transactions data

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns

    parser       : dict with instructions for processing the raw tx file

                    - 'input_type' : 'credit_debit' or 'net_amt'

                    - 'date_format': eg "%d/%m/%Y"

                    - 'map'        : dict of map for column labels
                                     (new labels are keys, old are values)

                    - 'debit_sign' : are debits shown as negative
                                     or positive numbers? (for net_amt inputs)
                                     - default is 'positive'

                 - mapping must cover following columns (i.e. new labels):

                       - net_amt: ['date', 'accX', 'accY', 'net_amt', 'ITEM']

                       - credit_debit: 'debit_amt', 'credit_amt'
                         replace 'net_amt'

                 - may optionally provide a mapping for 'balance'

    """

    # check parser matches input df
    matches = {col: (col in new_tx_df.columns)
                   for col in parser['map'].values()}
    if not all(matches.values()):
        print('parser map does not match new_tx_df columns')
        print('parser map values:', list(parser['map'].values()))
        print('new_tx_df.columns', list(new_tx_df.columns))

        return

    # organise columns using parser, and add '_item' column
    df = new_tx_df[list(parser['map'].values())].copy()
    df.columns = parser['map'].keys()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    df['_item'] = df['ITEM'].str.lower().str.strip() 

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        df['debit_amt'] = pd.to_numeric(df['debit_amt'], errors='coerce')
        df['credit_amt'] = pd.to_numeric(df['credit_amt'], errors='coerce')

        df['net_amt'] = (df['debit_amt']
                             .subtract(df['credit_amt'], fill_value=0))

    if parser.get('debit_sign', 'positive') == 'positive':
        df['net_amt'] *= -1
        
    cols = ['ITEM', '_item', 'net_amt']

    if 'balance' in parser['map']:
        cols.append('balance')

    df['source'] = new_tx_df['source'].values
    cols.append['source']

    return df[cols]


#------------------------------------------------------------------------------

def balance_continuum(df):
    """Returns an array with zeroes where balances are consistent with
    net_amounts.

    If balances are consistent, then:
        bal[n]  = bal[n-1] + net_amt[n]
        0 = bal[n] - (bal[n-1] + net_amt[n])
    """
    continuum = (df.balance[1:].values 
            - (df.net_amt[1:].values
              + df.balance[:-1].values))

    continuum[pd.np.abs(continuum) < 10**-3] = 0

    print('bc1')

    return pd.np.concatenate([[0], continuum])



#------------------------------------------------------------------------------
    

def assign_targets(_items, account,
                   cat_db=None, unknowns_db=None, fuzzy_db=None,
                   fuzzymatch=True, fuzzy_threshold=75):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the 'mode' of the match) vs ref dbs (loaded in RAM)
    - returns list of tuples: (hit target, mode of assignment)

    """

    results = []
    for _item in _items:


        #    TEST                     -> TUPLE TO APPEND TO RESULTS
        # 1. is in unknowns_db?       -> ('unknown', 'old unknown')
        # 2. is in cat_db?            -> (<the hit>, 'known'      )
        # 3. is in fuzzy_db?          -> (<the hit>, 'old fuzzy'  )
        # 4. fuzzy match in tx_db?    -> (<the hit>, 'new fuzzy'  )
        # 5. ..else assign 'unknown'  -> ('unknown', 'new unknown')

        if (unknowns_db is not None
              and len(unknowns_db) > 0
              and unknowns_db.index.contains(_item)):

            results.append(('unknown', 'old unknown'))
            continue

        if cat_db is not None and cat_db.index.contains(_item):
            hits = cat_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'known'))
            continue

        if fuzzy_db is not None and fuzzy_db.index.contains(_item):
            hits = fuzzy_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'old fuzzy'))
            continue

        if fuzzymatch and cat_db is not None:
            best_match, score = process.extractOne(_item, cat_db.index.values,
                                                   scorer=fuzz.token_set_ratio)
            if score >= fuzzy_threshold:
                hits = cat_db.loc[[best_match]]
                results.append((pick_match(best_match, account, hits), 'new fuzzy'))
                continue

        results.append(('unknown', 'new unknown'))

    return results


#------------------------------------------------------------------------------

def pick_match(item, account, hits, return_col='accY'):
    """Returns match for item in sub_df of hits, giving preference for hits
    in home account
    """
    # if only one match, return it
    if len(hits) == 1:
        return hits.loc[item,return_col]
    
    # if more than one, look for a hit in home account
    if len(hits) > 1:
        home_acc_hits = hits[hits['accX']==account]

        # if any home hits, return the first - works even if multiple
        if len(home_acc_hits) > 0:
            return home_acc_hits.iloc[0].loc[return_col]

        # if no home account hits, just return the first assigned hit
        else:
            return hits.iloc[0].loc[return_col]



def tidy(df):
    orig_index = df.index.names
    out = df.reset_index().drop_duplicates()
    out = out.sort_values(list(out.columns))
    return out.set_index(orig_index)



