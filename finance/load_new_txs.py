import pandas as pd
import numpy as np
import os
from os import chdir
from shutil import move
from pathlib import Path
from pprint import pprint
from fuzzywuzzy import fuzz, process

test_tag = '***TEST: '

from finance.init_scripts import get_dirs

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

    Returns a df but does all its work on disk anyway.
    """

    main_dir = Path(main_dir).absolute()

    # load the dbs (a dict of dfs)
    dbs = get_dbs(main_dir)

    for acc_path in (main_dir / 'tx_accounts').iterdir():
        print('entering', acc_path.name)

        prepare_new_csv_files(acc_path.absolute())

        dirs = get_dirs(acc_path)

        for dir in dirs:
            print(("- " + dir).ljust(20), str(len(dirs[dir])).rjust(3))


        if dirs['new_csvs']:

            df = load_new_csv_files(dirs['new_csvs'], acc_path)
            print('df len', len(df))
            df = trim_df(df, acc_path, dbs['tx_db'],
                         write_out_dbs=write_out_dbs,
                         write_out_path=write_out_path)
            print('df len', len(df))
            df = add_target_acc_col(df, acc_path, dbs)
            print('df len', len(df))

            # check for discontinuity only if account reports balance
            # df_check = check_df(df, acc_path)

            # update the dbs
            dbs['fuzzy_db']    = update_fuzzy_db(df, dbs['fuzzy_db'])
            dbs['unknowns_db'] = update_unknowns_db(df, dbs['unknowns_db'])
            dbs['tx_db']       = update_tx_db(df, dbs['tx_db'])

            # move the processed tx files to another folder
            # only if write_out_dbs I guess
            if move_new_txs:
                for f in dirs['new_csvs']:
                    move(f, acc_path / 'processed_csvs' / f.name)
        else:
            print('did not find dirs["new_csvs"]')

    # save dbs to disc
    if write_out_dbs:
        if write_out_path is None:
            out_dir = main_dir
        else:
            out_dir = Path(write_out_path)

        for db in dbs:
            dbs[db].to_csv(out_dir / db + '_db.csv')

    if return_dbs:
        return(dbs)


def load_new_csv_files(new_txs_files, acc_path):
    df = pd.concat([pd.read_csv(x) for x in new_txs_files])
    parser = pd.read_pickle(acc_path / 'parser.pkl')
    df = format_new_txs(df, account_name=acc_path.name, parser=parser)
    return df.sort_values('date')


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
        parser = pd.read_pickle(acc_path / 'parser.pkl')
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


def get_dbs(dir_path=None):

    if dir_path is None:
        dir_path = Path('.')
    else:
        dir_path = Path(dir_path)

    dbs = {}

    dbs['unknowns_db'] = pd.read_csv(dir_path / 'unknowns_db.csv',
                                     index_col='_item')
    dbs['tx_db']       = pd.read_csv(dir_path / 'tx_db.csv',
                                     index_col='date')
    dbs['fuzzy_db']    = pd.read_csv(dir_path / 'fuzzy_db.csv',
                                     index_col='_item')
    dbs['cat_db']      = pd.read_csv(dir_path / 'cat_db.csv',
                                     index_col='_item')

    dbs['tx_db'].index = pd.to_datetime(dbs['tx_db'].index)

    return dbs


def prepare_new_csv_files(dir_path):
    prep_script_path = dir_path.absolute() / 'prep.py'
    if prep_script_path.exists():
        # need to move to directory as can't pass a path to the prep.py script
        pwd = Path.cwd()
        print('pwd1', Path().cwd())
        chdir(dir_path)
        print('pwd2', Path().cwd())
        print('prep_script_path', prep_script_path)
        exec(open(prep_script_path).read())

        chdir(pwd)
        print('pwd3', Path().cwd())
    else:
        print('cannot find', prep_script_path)

##############################################################################

def load_new_test(seed_df=None, targets=None, main_dir=None):
    """
    test sequence supposed to mirror load_new but with prints
    and asserts

    really needs refactoring to more closely mirror load_new
    """

    test = False
    if seed_df is not None and targets is not None:
        test = True

    if main_dir is None:
        main_dir = Path('.')

    else:
        main_dir = Path(main_dir)

    # begin with a test folder structure, as generated by populate_test_project,
    # and the seed df that was used to populate it

    #-------------------------------------------------------------------------
    _prtitle('-- 0. SETTING UP')

    #-------------------------------------------------------------------------
    _prtitle('-- 0.1 reading in the seed_df')


    #-------------------------------------------------------------------------
    _prtitle('-- 0.2 reading in the db csvs')

    unknowns_db, tx_db, fuzzy_db, cat_db = get_dbs(main_dir)

    #-------------------------------------------------------------------------
    _prtitle('-- 1. PROCESS ANY NEW TRANSACTIONS IN TX_ACCOUNTS FILE STRUCTURE')

    os.chdir('tx_accounts')
    print('\nFound tx accounts:', os.listdir())

    for acc in os.listdir():
        _prtitle('PROCESSING', acc)
        os.chdir(acc)

        # just continue if no new files (remembering to exit account folder)
        if not os.listdir('new_txs'):
            print('  ..no new files')
            os.chdir('..')
            continue

        # otherwise process them
        print('  ..found new files', os.listdir('new_txs'))

        if test:
            seed_df_acc = seed_df.loc[seed_df['accX'] == acc].copy()
            seed_df_acc['balance'] = seed_df_acc['net_amt'].cumsum()
            print('\n---> seed_df for this acc:\n', seed_df_acc)

        #----------------------------------------------------------------------
        _prtitle(' i. Look for prep.py and execute if present', acc)

        if os.path.exists('prep.py'):
            print('\n' + test_tag + 'Found a prep.py, executing it..', end='')
            exec(open('prep.py').read())
            # print('contents of prep.py\n', open('prep.py').read())
            if test:
                assert os.path.exists('prep.exec.out')
            print('..OK')

        #----------------------------------------------------------------------
        _prtitle(' ii. Load new tx csvs and concat, using pandas', acc)

        os.chdir('new_txs')
        df = pd.concat([pd.read_csv(x) for x in os.listdir()])
        print('\n---> loaded csv files and concatted:\n', df)
        os.chdir('..')

        #----------------------------------------------------------------------
        _prtitle('  iii. Format and structure the csv using parser', acc)

        parser = pd.read_pickle('parser.pkl')
        print('\n---> loaded parser:'); pprint(parser)
        df = format_new_txs(df, account_name=acc, parser=parser)
        df = df.sort_values('date')
        print('\n---> df after format_new_txs\n', df)

        #----------------------------------------------------------------------
        _prtitle(' iv. Check balance continuum and duplicates in aggregated txs', acc)

        print('balance continuum', balance_continuum(df))

        if balance_continuum(df).sum():
            print('WARNING:', acc, 'has a balance discontinuity')

        print('duplicates:', df.duplicated().values)

        if df.duplicated().values.sum():
            print('WARNING:', acc, 'has duplicated values')


        #----------------------------------------------------------------------
        _prtitle(' v. Append to prev_txs.csv, net of any overlap', acc)

        if test:
            # get the target for comparison from the seed df
            seed_df_new_cols = ['ITEM', '_item', 'net_amt', 'balance']
            seed_df_new = seed_df_acc.loc[seed_df_acc.prev
                                          == 0, seed_df_new_cols]
            print('\n---> real new txs from seed')
            print(seed_df_new)

        # load the prev_txs
        prev_txs_df = pd.read_csv('prev_txs.csv', parse_dates=['date'],
                                            dayfirst=True, index_col='date')
        print('\n---> prev_txs_df\n', prev_txs_df)

        # get the trimmed df and run the test
        df = trim_overlap(prev_txs_df, df)
        print('\n---> df after trim\n', df)
        if test:
            print('\n---> non-prevs from seed (which should be the same)\n',
                      seed_df_new)
            print('\n' + test_tag + 'overlap removal from df..', end='')
            db_compare(df, seed_df_new)
            assert df.equals(seed_df_new)
            print(' ..OK')

        df.to_csv('prev_txs.csv', mode='a', header=False,
                                    date_format=parser['date_format'])

        print('\n---> saved prev_txs', pd.read_csv('prev_txs.csv',
                                      parse_dates=['date'], index_col='date'))

        #----------------------------------------------------------------------
        _prtitle(' vi. Compute the target accounts for new items', acc)

        accYs = assign_targets(df._item, acc,
                                    unknowns_db=unknowns_db,
                                    fuzzy_db=fuzzy_db,
                                    cat_db=cat_db,
                                   )
        print('\naccY targets assigned\n', accYs)

        # make a df with accY, accY and mode columns
        df['accX'] = acc
        df['accY'] = [x[0] for x in accYs]
        df['mode'] = [x[1] for x in accYs]
        print('\n---> new txs with accY and mode\n', df)

        #----------------------------------------------------------------------
        _prtitle(' vii. Append any new fuzzy matches or unknowns to corresponding db', acc)

        # get fuzzy matches
        print('\ninitial fuzzy db\n', fuzzy_db)
        new_fuzzies = (df.loc[df['mode'] == 'new fuzzy']
                         .set_index('_item', drop=True))
        new_fuzzies['status'] = 'unconfirmed'
        new_fuzzies = new_fuzzies[fuzzy_db.columns]
        print('\nnew fuzzy matches\n', new_fuzzies)
        fuzzy_db = tidy(fuzzy_db.append(new_fuzzies))
        print('\nnew fuzzy db\n', fuzzy_db)

        # get unknowns
        print('\n' + '-'*30 + '\ninitial unknowns db\n', unknowns_db)
        print('\ninitial df\n', df)
        new_unknowns = (df.loc[df['mode'] == 'new unknown']
                         .set_index('_item', drop=True))
        print('\nnew unknowns\n', new_unknowns)
        unknowns_db = unknowns_db.append(new_unknowns[unknowns_db.columns])
        unknowns_db = tidy(unknowns_db)
        print('\nnew unknowns db\n', unknowns_db)

        #----------------------------------------------------------------------
        _prtitle(' viii. Append any new txs to tx_db', acc)

        max_current = int(tx_db['id'].max()) if len(tx_db>0) else 100

        df['id'] = np.arange(max_current + 1,
                              max_current + 1 + len(df)).astype(int)

        print('\nfinal new txs df\n', df)

        tx_db = tx_db.append(df[tx_db.columns])

        print('\ntx_db after appending df\n', tx_db)

        os.chdir('..')


    #-------------------------------------------------------------------------
    _prtitle('saving dbs to disk (tx, fuzzy, unknown only)')

    # move back up, from tx_accounts to main project directory
    os.chdir('..')

    tx_db.to_csv('tx_db.csv', date_format=parser['date_format'])
    fuzzy_db.to_csv('fuzzy_db.csv')
    unknowns_db.to_csv('unknowns_db.csv')


    #-------------------------------------------------------------------------
    if test:
        _prtitle(' FINAL TESTS')


        def _compare(stage, dbname, df):
            """helper function to put together tests for each db"""

            print('\n' + test_tag + 'testing', dbname, '- at stage', stage)

            target_df = targets[stage][dbname]
            target_df = (target_df.sort_values(by=list(target_df
                                                       .columns)).sort_index())
            test_df = df[target_df.columns].copy()
            test_df = test_df.sort_values(by=list(test_df.columns)).sort_index()

            print('\ntest df from csv\n', test_df)
            print('\ntarget df\n', target_df)

            assert target_df.equals(test_df)
            print(' ..OK******')

        tx_db = pd.read_csv('tx_db.csv', parse_dates=['date'],
                                                dayfirst=True, index_col='date')
        _compare('loaded', 'tx_db', tx_db)

        fuzzy_db = pd.read_csv('fuzzy_db.csv', index_col='_item')
        _compare('loaded', 'fuzzy_db', fuzzy_db)

        unknowns_db = pd.read_csv('unknowns_db.csv', index_col='_item')
        _compare('loaded', 'unknowns_db', unknowns_db)


##############################################################################

def main(new_tx_paths, account_name, parser,
         tx_db_path    = 'tx_db.csv',
         cat_db_path   = '../persistent_cat_db.csv', 
         unknowns_path = 'unknowns_db.csv',
         fuzzy_db_path = 'fuzzy_db.csv', fuzzymatch=True):
    """Loads new transactions from input csvs in tx_db_path.

    Assigns categories by checking againts dbs for knowns,
    unknowns and previous fuzzy matches - or by carrying out
    a new fuzzy match.

    Updates dbs, including the main tx_db
    """

    # load db files to RAM
    tx_db       = pd.read_csv(tx_db_path,    index_col='date')
    cat_db      = pd.read_csv(cat_db_path,   index_col='_item')
    unknowns_db = pd.read_csv(unknowns_path, index_col='_item')
    fuzzy_db    = pd.read_csv(fuzzy_db_path, index_col='_item')

    # parse the new transactions
    new_txs = parse_new_txs(new_tx_paths, account_name, parser)

    # add categories and modes (source of categorisation)
    assignments = assign_targets(new_txs['_item'], account_name,
                                 cat_db, unknowns_db, fuzzy_db)

    new_txs = new_txs.join(pd.DataFrame(assignments, columns=['accY', 'mode']))

    # append the new unknowns to unknowns_db
    new_unknowns = new_txs.loc[new_txs['mode'] == 'new unknown',
                               ['_item', 'accY']]
    new_unknowns['accX'] = account_name

    unknowns_db = unknowns_db.append(new_unknowns[['_item', 'accX', 'accY']]
                               .set_index('_item', drop=True))
    unknowns_db = unknowns_db.drop_duplicates()
    unknowns_db.to_csv(unknowns_path)


    # append the new fuzzy matches to fuzzy_db
    new_fuzzies = new_txs.loc[new_txs['mode'] == 'new fuzzy', ['_item', 'accY']]
    new_fuzzies['status'] = 'unconfirmed'
    new_fuzzies['accX'] = account_name

    fuzzy_db = fuzzy_db.append(new_fuzzies[['_item', 'accX', 'accY', 'status']]
                               .set_index('_item', drop=True))
    fuzzy_db = fuzzy_db.drop_duplicates()
    fuzzy_db.to_csv(fuzzy_db_path)

    # finally append the new txs to the tx_db (with unique IDs)
    max_current = int(tx_db['id'].max()) if len(tx_db>0) else 100

    new_txs['id'] = np.arange(max_current + 1,
                              max_current + 1 + len(new_txs)).astype(int)

    new_txs['accX'] = account_name

    new_txs = (new_txs[['date', 'accX', 'accY', 'net_amt', 'ITEM', '_item',
                        'id', 'mode']].set_index('date'))

    tx_db = tx_db.append(new_txs)
    tx_db.to_csv(tx_db_path)


#------------------------------------------------------------------------------

def make_parser(input_type = 'credit_debit',
                  date_format = '%d/%m/%Y',
                  debit_sign = 'positive',
                  date = 'date',
                  ITEM = 'ITEM',
                  net_amt = 'net_amt',
                  credit_amt = 'credit_amt',
                  debit_amt = 'debit_amt',
                  balance = None,
               ):
    """Generate a parser dict for controlling import of new txs from csv.

    input_type      : 'debit_credit' or 'net_amt'
    date_format     : strftime structure, eg see default
    debit_sign      : if net_amt, are debits shown as 'positive' or 'negative'

    the rest are column name mappings - that is, the names in the input csv
    for the columns corresponding to 'date' 'ITEM', 'net_amt' etc

    Will automatically remove mappings that are not reqd, eg will remove 'net_amt'
    if the input type is 'debit_credit'.
    """

    parser = dict(input_type = input_type,
                  date_format = date_format,
                  debit_sign = debit_sign,
                  map = dict(date = date,
                             ITEM = ITEM,
                             net_amt = net_amt,
                             credit_amt = credit_amt,
                             debit_amt = debit_amt,
                            )
                 )

    if input_type == 'credit_debit':
        del parser['map']['net_amt']

    if input_type == 'net_amt':
        del parser['map']['credit_amt']
        del parser['map']['debit_amt']

    if balance is not None:
        parser['map']['balance'] = balance

    return parser


#------------------------------------------------------------------------------

def format_new_txs(new_tx_df, account_name, parser):

    """Return a tx_df in standard format, with date index,
    and columns: 'date', 'ITEM', '_item', 'net_amt' 

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

    return df[cols]


#------------------------------------------------------------------------------

def balance_continuum(df):
    """Returns an array with zeroes where balances are consistent with
    net_amounts.

    If balances are consistent, then:
        bal[n]  = bal[n-1] + net_amt[n]
        0 = bal[n] - (bal[n-1] + net_amt[n])
    """
    return (df.balance[1:].values 
            - (df.net_amt[1:].values
              + df.balance[:-1].values))



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

#------------------------------------------------------------------------------

def trim_overlap(prev_txs_df, new_txs_df):
    """
    Obsolete now
    """
    # get last tx of prev
    # get last date of prev
    # if not in dates in new then return
    # make sub_df for that date in new_txs_df
    #
    if len(prev_txs_df) == 0:
        return new_txs_df.copy()

    df = new_txs_df.reset_index()
    print('in trim, df\n', prev_txs_df.reset_index())
    last_tx_of_prev = tuple(prev_txs_df.reset_index().iloc[-1])
    match_index = -1
    df_tuples = [tuple(y) for y in df.values]
    for i, x in enumerate(df_tuples):
        if x == last_tx_of_prev:
            match_index = i
    if match_index != -1:
        return new_txs_df.iloc[(match_index + 1):].copy()
    else:
        return new_txs_df.copy()


#------------------------------------------------------------------------------
# helpers

def tidy(df):
    orig_index = df.index.names
    out = df.reset_index().drop_duplicates()
    out = out.sort_values(list(out.columns))
    return out.set_index(orig_index)


def db_compare(target, test, assertion=False):
    """
    Compares two dataframes.
    First naively applies target.equals(test)

    If fails then moves on to trying by cell.
    """

    if not assertion:
        return target.eq(test)

    if target.equals(test):
        assert True
        print('equality by pd.equals()')
        return

    for col in target.columns:
        for row in target.index:

            x = test.loc[row, col]
            y = target.loc[row, col]

            # weird case of Nans
            if str(x) == 'nan' and str(y) == 'nan':
                assert True

            else:
                assert test.loc[row, col] == target.loc[row, col]

    # if got this far, then assertions passed
    print('equality by cell comparison')

