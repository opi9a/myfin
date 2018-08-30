import pandas as pd
import numpy as np
import os
from shutil import copyfile, rmtree
from datetime import datetime as dt

from finance.load_new_txs import make_parser

def populate_test_project(seed_df, proj_name=None, return_df=False):
    """Using a seed_df source file with transactions data and other info, 
    create and populate a project, with transaction accounts - including
    new_txs, dbs etc
    """

    init_dir = os.getcwd()
    df = seed_df.reset_index()
    df['_item'] = df['ITEM'].str.lower().str.strip()

    # default is to start in proj dir but move there if not
    if proj_name is not None:
        os.chdir(proj_name)

    # First copy to the dbs at highest folder level, as reqd
    unknowns = df.loc[df.db=='unknown', ['_item', 'accX', 'accY']]
    unknowns.to_csv('unknowns_db.csv', mode='a', header=False, index=False)

    knowns = df.loc[df.db=='known', ['_item', 'accX', 'accY']]
    knowns.to_csv('cat_db.csv', mode='a', header=False, index=False)

    fuzzy = df.loc[df.db=='fuzzy', ['_item', 'accX', 'accY']].copy()
    fuzzy['status'] = 'unconfirmed'
    fuzzy.to_csv('fuzzy_db.csv', mode='a', header=False, index=False)

    tx_db = pd.read_csv('tx_db.csv')
    max_current = int(tx_db['id'].max()) if len(tx_db>0) else 100

    prev_txs = df.loc[df['prev'] == 1].copy()
    prev_txs['id'] = np.arange(max_current + 1,
                               max_current + 1 + len(prev_txs)).astype(int)
    prev_txs['mode'] = 'x'
    (prev_txs.loc[:,['date', 'accX', 'accY', 'net_amt', 'ITEM',
                     '_item', 'id', 'mode']]
            .to_csv('tx_db.csv', mode='a', header=False, index=False))

    # (also add any new fuzzy targets to cat_db)
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

        # write the prev existing txs to prev_txs
        prev_tx_cols = ['date', 'ITEM', '_item', 'net_amt', 'balance']
        (txs.loc[txs['prev'] == 1, prev_tx_cols]
            .to_csv('prev_txs.csv', mode='a', header=False, index=False))

        # now the new_txs, in accs specified by 'new_file_index'
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

        # - now generate the new_txs files (in the new_txs dir)
        os.chdir('new_txs')
        for i in new.t_new_file_index.unique():
            new_name = 'new_txs' + str(int(i)) + '.csv'
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


def initialise_project(proj_name, overwrite_existing=False, cat_db_to_import=None):

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
    init_dir = os.getcwd()
    print('\ninitialising project, dir is:', init_dir)
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

    os.chdir(init_dir)

    return os.path.abspath(proj_name)


def initialise_tx_account(acc_name, has_balance=True):
    """Starting in an empty tx_accounts dir, 
    create folder structure for a new tx_account:
        - proj_path/tx_accounts/acc_name/
            - new_txs/
                - <any new files>
            - prev_txs/
                - <files after processing>
            - prev_txs.csv
            - parser.pkl
            - prep.py <optional, add later>

    """
    loglist = []
    init_dir = os.getcwd()

    # check in a tx_accounts dir
    if os.path.basename(init_dir) != 'tx_accounts':
        print('not in a tx_accounts directory, exiting')

    os.mkdir(acc_name)
    os.chdir(acc_name)
    addlog(loglist, 'initialising tx_account: ' + os.getcwd())

    # make the empty tx dirs
    os.mkdir('new_txs')
    os.mkdir('prev_txs')
    addlog(loglist, 'made empty new_txs folder in ' + acc_name)
    addlog(loglist, 'made empty prev_txs folder in ' + acc_name)


    # make the empty prev_txs.csv
    cols = ['date', 'ITEM', '_item', 'net_amt'] 

    if has_balance:
        cols.append('balance')

    pd.DataFrame(columns=cols).to_csv('prev_txs.csv', index=False)

    addlog(loglist, 'made empty prev_txs.csv in ' + acc_name)

    os.chdir(init_dir)

    addlog(loglist, 'returning to init_dir: ' + os.getcwd())

    # once back in tx_accounts directory, write log out in dir above
    writelog(loglist, logpath='..')


def tstamp(width=26):
    return "[ " + str(dt.now()).ljust(width) + " ] "


def writelog(loglist, logpath=None):
                
    if logpath is None:
        logpath = os.getcwd()

    path_out = os.path.join(logpath, 'log.txt')
    print("\n".join(loglist).ljust(30), file=open(path_out, 'a'))


def addlog(loglist, logstring):
    loglist.append(tstamp() + logstring)

