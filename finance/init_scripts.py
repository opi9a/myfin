import pandas as pd
import numpy as np
import os
from pathlib import Path
from shutil import copyfile, rmtree
from datetime import datetime as dt


def check_seed(seed_df_path):
    print('\nChecking seed.. ', end='')

    df = pd.read_csv(seed_df_path, parse_dates=['date'],
                     dayfirst=True, index_col='date')

    # whitelist designations in fuzzy_db (and knowns, shd not have any)
    mask = (~df['update_action'].isnull()) & (df['db'] != 'unknown')
    whitelist = {'rejected', 'confirmed'}

    if not df.loc[mask, 'update_action'].isin(whitelist).all():
        print('\nSeed df update actions out of whitelist:')
        print(set(df.loc[mask, 'update_action'].values) - whitelist)
        return 1

    # if there is a fuzzed_ITEM, the db must be None (or it
    # will not go through fuzzy matching)
    mask = (~df['fuzzed_ITEM'].isnull()) & (df['db'] != 'None')

    if len(df.loc[mask]):
        print("fuzzed_ITEM also appearing in a db")
        return 1

    # update actions for unknowns (new accYs) must correspond to accY col
    mask = (~df['update_action'].isnull()) & (df['db'] == 'unknown')

    if not df.loc[mask, 'update_action'].equals(df.loc[mask, 'accY']):
        print("Update_action field of seed_df doesn't match accYs")
        return 1

    # types of columns are right
    if not df.index.is_all_dates:
        print('Seed df index is not dates')
        return 1

    if not np.issubdtype(df['net_amt'], np.number):
        print('Seed df net_amt is not numeric')
        return 1

    if not df['prev'].isin({0, 1}).all():
        print('Seed df prev is not all 0 or 1')
        return 1

    if not df['db'].isin({'unknown', 'known', 'fuzzy', 'None'}).all():
        print('dbs not recognised')
        return 1

    print('..OK')

    return 0


def xmake_targets(seed_df_path, return_seed=False):
    # load the seed df
    cols = ['_item', 'accX', 'accY']
    out = dict(loaded={}, updated={})

    seed = pd.read_csv(seed_df_path, parse_dates=['date'], dayfirst=True,
                     index_col='date')

    seed['_item'] = seed['ITEM'].str.lower().str.strip()

    # way to unknown:
        # db==unknown
        # db==None and no fuzzed_ITEM
    mask1 = (seed['db'] == 'unknown')
    mask2 = (seed['db'] == 'None') & (seed['fuzzed_ITEM'].isnull())
    mask = mask1 | mask2
    df = seed.loc[mask, ['_item', 'accX']]
    df = df.reset_index(drop=True).set_index('_item')
    df['accY'] = 'unknown'
    out['loaded']['unknowns_db'] = tidy(df)

    # knowns: rows where db==known, and make a target for any fuzzed_ITEMs
    mask = (seed['db'] == 'known')
    df = seed.loc[mask, ['_item', 'accX', 'accY']]
    df = df.reset_index(drop=True).set_index('_item')

    # add rows for any fuzzed_ITEMs
    fuzzy_targets = seed.loc[~seed['fuzzed_ITEM'].isnull(),
                             ['fuzzed_ITEM', 'accX', 'accY']].copy()

    fuzzy_targets['_item'] = (fuzzy_targets['fuzzed_ITEM']
                                        .str.lower().str.strip())
    fuzzy_targets = tidy(fuzzy_targets.set_index('_item', drop=True))
    df = df.append(fuzzy_targets[['accX', 'accY']])
    out['loaded']['cat_db'] = tidy(df)

    # fuzzy_db: rows where db==fuzzy and any new fuzzies
    mask = (seed['db'] == 'fuzzy') | (~seed['fuzzed_ITEM'].isnull())
    df = seed.loc[mask, ['_item', 'accX', 'accY']]
    df = df.reset_index(drop=True).set_index('_item')
    out['loaded']['fuzzy_db'] = tidy(df)

    # tx_db: copy seed, but overwrite any unknowns (incl after fuzzy matches)
    df = seed.copy()
    df.loc[df['db'] == 'unknown', 'accY'] = 'unknown'
    df.loc[(df['db'] == 'None') &
           (df['fuzzed_ITEM'].isnull()), 'accY'] = 'unknown'
    df = df[['accX', 'accY', 'net_amt', 'ITEM', '_item']]

    out['loaded']['tx_db'] = df

    # UPDATED

    # unknowns:
        # - start in unknown db and don't have update
        # - start in None and don't have fuzzed_ITEM
        # - update_action is 'rejected'
    mask1 = (seed['db'] == 'unknown') & (seed['update_action'].isnull())
    mask2 = (seed['db'] == 'None') & (seed['fuzzed_ITEM'].isnull())
    mask3 = (seed['update_action'] == 'rejected')
    mask = mask1 | mask2 | mask3

    print('in xchanges with unknowns')
    print('seed.loc[mask]', seed.loc[mask, ['_item', 'accX']])

    df = seed.loc[mask, ['_item', 'accX']]
    df = df.reset_index(drop=True).set_index('_item')
    df['accY'] = 'unknown'
    out['updated']['unknowns_db'] = tidy(df)
    print(tidy(df))


    # fuzzy:
        # - start in fuzzy and no update
        # - start in None but have fuzzed_ITEM and no update
    mask1 = (seed['db'] == 'fuzzy') & (seed['update_action'].isnull())
    mask2 = ((seed['db'] == 'None') & (~seed['fuzzed_ITEM'].isnull())
                                    & (seed['update_action'].isnull()))
    mask = mask1 | mask2

    df = seed.loc[mask, ['_item', 'accX', 'accY']]
    df = df.reset_index(drop=True).set_index('_item')
    out['updated']['fuzzy_db'] = tidy(df)

    # cat_db:
        # - start in known
        # - update_action is 'confirmed'
        # - have fuzzed_ITEM with no update_action
    mask1 = (seed['db'] == 'known')
    mask2 = (seed['update_action'] == 'confirmed')
    mask3 = (~seed['fuzzed_ITEM'].isnull()) & (seed['update_action'].isnull())
    mask = mask1 | mask2 | mask3

    df = seed.loc[mask, ['_item', 'accX', 'accY']]
    df = df.reset_index(drop=True).set_index('_item')
    out['updated']['cat_db'] = tidy(df) 

    # tx_db - all rows, accY as original, except:
        # paths to known (accY is original):
            # db=known
            # fuzzed_ITEM and update != rejected
            # update_action is not null, and not rejected
    df = seed.copy()

    mask1 = (seed['db'] == 'known')
    mask2 = ((~seed['fuzzed_ITEM'].isnull()) 
                    & (seed['update_action'] !='rejected'))
    mask3 = ((~seed['update_action'].isnull()) & 
                    (seed['update_action'] !='rejected')) 

    mask = mask1 | mask2 | mask3

    #simpler to turn it into unknowns
    mask = ~mask

    df.loc[mask, 'accY'] = 'unknown'
    df.loc[(df['db'] == 'None') &
           (df['fuzzed_ITEM'].isnull()), 'accY'] = 'unknown'
    df = df[['accX', 'accY', 'net_amt', 'ITEM', '_item']]

    out['updated']['tx_db'] = df

    if return_seed:
        return out, seed
    else:
        return out


def edit_db(db, tuples_to_change, new_vals=None):
    if isinstance(new_vals, str):
        new_vals = [new_vals]

    orig_index = db.index.names

    print('\ndb1\n', db)
    print('\ntuples\n', tuple(tuples_to_change))
    print('\nnew_vals\n', new_vals)

    if orig_index != 'date':
        db = deduple(db)

    db = db.reset_index().set_index(['_item', 'accX'])
    print('\ndb2\n', db)

    if new_vals is None:
        db = db.drop(tuples_to_change)

    elif tuples_to_change.isin(db.index).all():
        db.loc[tuples_to_change, 'accY'] = new_vals

    else:
        print('\ntuples to change\n', tuple(tuples_to_change))
        print('\nlen(tuples)\n', len(tuples_to_change))
        print('\nlen(new_vals)\n', len(new_vals))
        print('\nnew_vals.values\n', new_vals.values)
        appendee = pd.DataFrame({'accY': new_vals.orig_accY}, index=tuples_to_change) 
        db = db.append(appendee)


    return db.reset_index().set_index(orig_index)



def populate_test_project(seed_df, proj_name=None, return_df=False):
    """Using a seed_df source file with transactions data and other info, 
    create and populate a project, with transaction accounts - including
    new_csvs, dbs etc
    """

    init_dir = os.getcwd()
    df = seed_df.reset_index()
    df['_item'] = df['ITEM'].str.lower().str.strip()

    # default is to start in proj dir but move there if not
    if proj_name is not None:
        os.chdir(proj_name)

    # First copy to the dbs at highest folder level, as reqd
    # - remembering to overwrite 'accY' when necessary
    unknowns = df.loc[df.db=='unknown', ['_item', 'accX', 'accY']]
    unknowns['accY'] = 'unknown'
    unknowns.to_csv('unknowns_db.csv', mode='a', header=False, index=False)

    knowns = df.loc[df.db=='known', ['_item', 'accX', 'accY']]
    knowns.to_csv('cat_db.csv', mode='a', header=False, index=False)

    fuzzy = df.loc[df.db=='fuzzy', ['_item', 'accX', 'accY']].copy()
    fuzzy['status'] = 'unconfirmed'
    fuzzy.to_csv('fuzzy_db.csv', mode='a', header=False, index=False)

    tx_db = pd.read_csv('tx_db.csv')
    max_current = int(tx_db['id'].max()) if len(tx_db>0) else 100

    processed_csvs = df.loc[df['prev'] == 1].copy()
    processed_csvs['id'] = np.arange(max_current + 1,
                               max_current + 1 + len(processed_csvs)).astype(int)
    processed_csvs['mode'] = 'x'

    # pre_txs becomes the initial tx_db 
    # - will need to overwrite with unknown if db=unknown or None
    mask = (processed_csvs['db']=='unknown') | (processed_csvs['db']=='None')
    processed_csvs.loc[mask,'accY'] = 'unknown'

    (processed_csvs.loc[:,['date', 'accX', 'accY', 'net_amt', 'ITEM',
                     '_item', 'id', 'mode']]
            .to_csv('tx_db.csv', mode='a', header=False, index=False))

    # also add any new fuzzy targets to cat_db
    new_fuzzy = df.loc[~df.fuzzed_ITEM.isnull(),
                       ['fuzzed_ITEM', 'accX', 'accY']]
    new_fuzzy.columns = ['_item', 'accX', 'accY']
    new_fuzzy.to_csv('cat_db.csv', mode='a', header=False, index=False)

    # move into the accounts folder
    os.chdir('tx_accounts')

    # now go through accounts, creating transaction files
    for acc in df.accX.unique():

        # create a folder structure for this account
        if not acc in os.listdir():
            initialise_tx_account(acc)

        # move into the account
        os.chdir(acc)

        # separate out the txs for this account, adding balance
        txs = df.loc[df['accX'] == acc].copy()
        txs['balance'] = txs.net_amt.cumsum()

        # write the prev existing txs to processed_csvs
        prev_tx_cols = ['date', 'ITEM', '_item', 'net_amt', 'balance']
        (txs.loc[txs['prev'] == 1, prev_tx_cols]
            .to_csv('processed_csvs.csv', mode='a', header=False, index=False))

        # return txs
        # now the new_csvs, in accs specified by 'new_file_index'
        new = txs.loc[txs['new_file_index'] > 0].copy()

        # - also want to transform columns and specify parser to reverse
        new.columns = ['t_'+x for x in new.columns]

        parser = make_parser(
                  input_type='net_amt',
                  debit_sign='negative',
                  date = 't_date',
                  ITEM = 't_ITEM',
                  net_amt = 't_net_amt',
                  credit_amt = 't_credit_amt',
                  debit_amt = 't_debit_amt',
                  balance = 't_balance')

        pd.to_pickle(parser, 'parser.pkl')

        # - now generate the new_csvs files (in the new_csvs dir)
        os.chdir('new_csvs')
        for i in new.t_new_file_index.unique():
            new_name = 'new_csvs' + str(int(i)) + '.csv'
            new_df = new.loc[new['t_new_file_index'] == i]
            new_df.to_csv(new_name, index=False)
        os.chdir('..')

        # will also need a prep.py file to execute
        with open('prep.py', 'w') as f:
            out_path = os.path.abspath(os.path.join(os.getcwd(),
                                                    'prep.exec.out'))
            f.write("with open('" + out_path + "', 'w') as f: f.write('0')\n")

        # exit the account
        os.chdir('..')

    os.chdir(init_dir)
    if return_df: return df


def initialise_project(proj_name, overwrite_existing=False,
                       parent_dir=None,
                       cat_db_to_import=None):

    """Required structure:

        proj_name/
        --- tx_db.csv
        --- cat_db.csv
        --- unknowns_db.csv
        --- fuzzy_db.csv
        --- log.txt
        --- tx_accounts/
        
        The csv files to contain column headings and index as appropriate, 
        but no rows.
    """

    # open a log list
    loglist = []

    # start from wherever called and make a directory with proj_name
    if parent_dir is None:
        parent_dir = os.getcwd()
    print('\ninitialising project in dir:', parent_dir)
    if not os.path.exists(proj_name):
        print('trying to create', proj_name)
        os.mkdir(proj_name)
    elif overwrite_existing:
        print(proj_name, 'exists already, overwriting it')
        rmtree(proj_name)
        os.mkdir(proj_name)
    else:
        print("A project with that name already exists in this directory.\
              pass 'overwrite_existing=True' to overwrite it")
        return 1

    os.chdir(proj_name)

    # make log first
    with open('log.txt', 'w') as f:
        f.write(tstamp() + 'initialising new project ' + proj_name + '\n')

    # handy set of columns 
    db_columns=['_item', 'accX', 'accY']

    # tx_db
    columns=['accX', 'accY', 'net_amt', 'ITEM', '_item', 'id', 'mode']
    ind = pd.DatetimeIndex(start='1/1/1970', periods=0, freq='D', name='date')
    df = pd.DataFrame(columns=columns, index=ind)
    df.to_csv('tx_db.csv', index=True)
    addlog(loglist, 'made empty tx_db.csv')

    # cat_db
    if cat_db_to_import is not None:
        cat_db_to_import = os.path.join('..', cat_db_to_import)
        copyfile(cat_db_to_import, 'cat_db.csv')
        addlog(loglist, 'imported cat_db from' + cat_db_to_import)

    else:
        pd.DataFrame(columns=db_columns).to_csv('cat_db.csv', index=False)
        addlog(loglist, 'made empty cat_db.csv')

    # tx_accounts
    os.mkdir('tx_accounts')
    addlog(loglist, 'made empty tx_accounts directory')

    # unknowns_db
    pd.DataFrame(columns=db_columns).to_csv('unknowns_db.csv', index=False)
    addlog(loglist, 'made empty unknowns_db.csv')
 
    # fuzzy_db
    db_columns.append('status')
    pd.DataFrame(columns=db_columns).to_csv('fuzzy_db.csv', index=False)
    addlog(loglist, 'made empty fuzzy_db.csv')

    # write out log
    writelog(loglist)

    os.chdir(parent_dir)

    return os.path.abspath(proj_name)


def initialise_tx_account(acc_path):
    """Create folder structure for a new tx_account in acc_path:
        - new_pre_csvs/
            - <any new files requiring processing to make csvs>
        - processed_pre_csvs/
            - <pre_csv files after processing>
        - new_csvs/
            - <any new files>
        - processed_csvs/
            - <files after processing>
        - parser.pkl
        - prep.py <optional, add later>

    """

    # check in a tx_accounts dir
    if acc_path.parent.name != 'tx_accounts':
        print('not in a tx_accounts directory, exiting')
        return

    if acc_path.exists():
        print(acc_path, 'already exists, exiting')
        return

    acc_path.mkdir()

    # make the empty tx dirs
    for d in ['new_pre_csvs', 'processed_pre_csvs',
              'new_csvs', 'processed_csvs']:
        (acc_path / d).mkdir()


def get_dirs(path):
    """
    Returns a dict whose keys are the directories in path.
    Values are lists of file paths.
    """
    dirs_out = {}

    for dir in path.iterdir():
        if dir.is_dir() and not dir.name.startswith('.'):
            dirs_out[dir.name] = list(dir.iterdir())

    return dirs_out


def clean_dir(dir_path, remove_self=False):
    """
    Removes all contents of a directory, and optionally the directory itself
    """

    print('clean_dir called with dir_path', dir_path)

    for f in dir_path.iterdir():
        if f.is_dir():
            clean_dir(f, remove_self=True)
        else:
            f.unlink()

    if remove_self:
        dir_path.rmdir()


def reset_tx_account(tx_account_path=None):
    """
    Restore a tx_account to unprocessed state, retaining original input
    data.

    If there are processed_pre_csvs, move these to new_pre_csvs and
    delete everything else.

    Otherwise move processed_csvs to new_csvs.
    """

    if tx_account_path is None:
        tx_account_path = Path('.')

    print('\nResetting', tx_account_path.absolute().name)

    dirs = get_dirs(tx_account_path)

    print('\nStructure before reset')
    for dir in dirs:
        print(("- " + dir).ljust(20), str(len(dirs[dir])).rjust(3))

    if dirs.get('processed_pre_csvs', False):
        print('\nfound processed_pre_csvs so move to new_pre_csvs '
              'and delete everything else')
        for f in dirs['processed_pre_csvs']:
            f.rename(tx_account_path / 'new_pre_csvs' / f.name)
        
        clean_dir(tx_account_path / 'new_csvs', False)
        clean_dir(tx_account_path / 'processed_csvs', False)

    if dirs.get('processed_csvs', False):
        print('\nfound processed_csvs so move to new_csvs')
        for f in dirs['processed_csvs']:
            f.rename(tx_account_path / 'new_csvs' / f.name)
        
    print('\nStructure after reset')
    dirs = get_dirs(tx_account_path)

    for dir in dirs:
        print(("- " + dir).ljust(20), str(len(dirs[dir])).rjust(3))


def tstamp(width=26):
    return "[ " + str(dt.now()).ljust(width) + " ] "


def writelog(loglist, logpath=None):
                
    if logpath is None:
        logpath = os.getcwd()

    path_out = os.path.join(logpath, 'log.txt')
    print("\n".join(loglist).ljust(30), file=open(path_out, 'a'))


def addlog(loglist, logstring):
    loglist.append(tstamp() + logstring)


def print_targets_dict(targets_dict, ind=None):
    if ind is None: ind = ""
    else: ind = str(ind)
    
    for s in targets_dict:
        for db in targets_dict[s]: print(f'{s}/{db}')
