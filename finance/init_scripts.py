import pandas as pd
import os
from shutil import copyfile
from datetime import datetime as dt

def populate_test_project(csv_generator, project_path=None):

    init_dir = os.getcwd()
    df = pd.read_csv(csv_generator)
    if project_path is not None:
        os.chdir(os.path.join(project_path))
        print('cd to project', project_path)
    print('pwd', os.getcwd())
    print('ls', os.listdir())

    for acc in df.accX.unique():
        print('now doing', acc)
        if not acc in os.listdir():
            initialise_tx_account(acc)
            print('creating', acc)
        print('pwd', os.getcwd())
        print(os.listdir())
        txs = df.loc[df['accX'] == acc]
        new = txs.loc[txs['new_prev'] == 'new']
        prev = txs.loc[txs['new_prev'] == 'prev']
        new_tx_dir = os.path.join('tx_accounts/', acc, 'new_txs/new.csv')
        print('new_tx_dir', new_tx_dir) 
        new.to_csv(new_tx_dir, index=False)
        prev.to_csv(os.path.join('tx_accounts', acc, 'prev_txs.csv'), index=False)

    print(os.listdir())

    os.chdir(init_dir)
    return 0


def initialise_project(proj_name, cat_db_to_import=None):
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
    if not os.path.exists(proj_name):
        os.mkdir(proj_name)
    else:
        print("A project with that name already exists in this directory")
        return 1

    # make log first
    with open(os.path.join(proj_name, 'log.txt'), 'w') as f:
        f.write(tstamp() + 'initialising new project ' + proj_name + '\n')

    # handy set of columns 
    db_columns=['_item', 'accX', 'accY']

    # tx_db
    columns=['accX', 'accY', 'net_amt', 'ITEM', '_item', 'id', 'mode']
    ind = pd.DatetimeIndex(start='1/1/1970', periods=0, freq='D', name='date')
    df = pd.DataFrame(columns=columns, index=ind)
    path_out = os.path.join(proj_name, 'tx_db.csv')
    df.to_csv(path_out, index=True)
    addlog(loglist, 'made empty tx_db.csv')

    # cat_db
    if cat_db_to_import is not None:
        copyfile(cat_db_to_import, os.path.join(proj_name, 'cat_db.csv'))
        addlog(loglist, 'imported cat_db from'
                                     + cat_db_to_import)

    else:
        path_out = os.path.join(proj_name, 'cat_db.csv')
        pd.DataFrame(columns=db_columns).to_csv(path_out, index=False)
        addlog(loglist, 'made empty cat_db.csv')

    # tx_accounts
    path_out = os.path.join(proj_name, 'tx_accounts')
    os.mkdir(path_out)
    addlog(loglist, 'made empty tx_accounts directory')

    # unknowns_db
    path_out = os.path.join(proj_name, 'unknowns_db.csv')
    pd.DataFrame(columns=db_columns).to_csv(path_out, index=False)
    addlog(loglist, 'made empty unknowns_db.csv')
 
    # fuzzy_db
    db_columns.append('status')
    path_out = os.path.join(proj_name, 'fuzzy_db.csv')
    pd.DataFrame(columns=db_columns).to_csv(path_out, index=False)
    addlog(loglist, 'made empty fuzzy_db.csv')

    # write out log
    path_out = os.path.join(proj_name, 'log.txt')
    writelog(loglist, proj_name)

    return os.path.abspath(proj_name)


def initialise_tx_account(acc_name, proj_name=None, has_balance=True):
    """Create folder structure for a new tx_account:
        - proj_name/tx_accounts/acc_name/
            - new_txs/
                - <any new files>
            - prev_txs/
                - <files after processing>
            - prev_txs.csv
            - parser.pkl
            - prep.py <optional, add later>

    """
    loglist = []

    if proj_name is None:
        proj_name = os.getcwd()

    print('in init_tx_acc')
    print('proj_name is', proj_name)
    acc_root = os.path.join(proj_name, 'tx_accounts', acc_name)
    print('acc_root', acc_root)
    print('abs path', os.path.abspath(acc_root))

    print('pwd', os.getcwd())
    print('ls', os.listdir())
    os.mkdir(acc_root)
    addlog(loglist, 'initialising new tx_account ' + acc_name)

    os.mkdir(os.path.join(acc_root, 'new_txs'))
    addlog(loglist, 'made empty new_txs folder in ' + acc_name)

    os.mkdir(os.path.join(acc_root, 'prev_txs'))

    cols = ['date', 'ITEM', '_item', 'net_amt'] 

    if has_balance:
        cols.append('balance')

    path_out = os.path.join(acc_root, 'prev_txs.csv')
    pd.DataFrame(columns=cols).to_csv(path_out, index=False)

    addlog(loglist, 'made empty prev_txs folder in ' + acc_name)
    addlog(loglist, 'made empty prev_txs.csv in ' + acc_name)
    writelog(loglist)


def tstamp(width=26):
    return "[ " + str(dt.now()).ljust(width) + " ] "


def writelog(loglist, proj_name=None, logpath='log.txt'):
                
    if proj_name is None:
        proj_name = os.getcwd()

    path_out = os.path.join(proj_name, logpath)
    print("\n".join(loglist).ljust(30), file=open(path_out, 'a'))


def addlog(loglist, logstring):
    loglist.append(tstamp() + logstring)

