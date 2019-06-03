import pandas as pd
import numpy as np
import os
from pathlib import Path
from shutil import copyfile, rmtree
import json
from datetime import datetime as dt


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
    ind = pd.DatetimeIndex(start='1/1/1970', periods=0, freq='D', name='date')
    df = pd.DataFrame(columns=TX_DB_COLUMNS, index=ind)
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
        - parser.json
        - prep.py <optional, add later>

    """

    # check making it in a tx_accounts dir
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
    path = Path(path)

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
    else:
        tx_account_path = Path(tx_account_path)

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


def make_parser(input_type = 'credit_debit',
                  date_format = '%d/%m/%Y',
                  debit_sign = 'positive',
                  date = 'date',
                  ITEM = 'ITEM',
                  net_amt = 'net_amt',
                  credit_amt = 'credit_amt',
                  debit_amt = 'debit_amt',
                  balance = None,
                  y_amt = None,
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

    elif input_type == 'net_amt':
        del parser['map']['credit_amt']
        del parser['map']['debit_amt']

    else:
        print('need an input type of either "net_amt" or "credit_debit"')

    if balance is not None:
        parser['map']['balance'] = balance

    if y_amt is not None:
        parser['map']['y_amt'] = y_amt

    return parser


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


def restore_using_new_csvs(new_csv_path=Path('new_csvs'), file_ext='.pdf',
                           delete_csvs=False):
    """
    Looks in new_csv_path for new csv files, and moves the corresponding 
    pre_csv file from processed_pre_csvs to new_pre_csvs    
    """

    print('restoring csvs in', new_csv_path)

    pdf_paths = []
    for csv in Path('new_csvs').iterdir(): 
        pdf_name = csv.name.replace('.csv', file_ext) 
        pdf_paths.append(Path('processed_pre_csvs', pdf_name))


    print('\nwill look for these pre_csvs:')
    print()

    for pdf_path in pdf_paths:
        print(' -', str(pdf_path).ljust(25), 'Exists:', pdf_path.exists())

    if input('\nrestore these to new_processed_csvs? ').lower() == 'y':
        print('\nok')
        for pdf_path in pdf_paths:
            if not pdf_path.exists():
                print('cannot find', str(pdf_path), 'to move it')
                continue
            new_path = Path('new_pre_csvs', pdf_path.name)
            print('renaming to', new_path)
            pdf_path.rename(new_path)
            print('success', new_path.exists())



    else:
        print('\nexiting')


def clear_dbs(acc_path=Path()):
    """
    Clears dbs except cat_db
    """

    acc_path = Path(acc_path)

    for db in DB_NAMES:
        if db != 'cat_db':
            db_path = acc_path / (db + '.csv')
            df = pd.read_csv(db_path, index_col=None).iloc[0:0,:]
            print(db, df)
            df.to_csv(db_path, index=False)

def tidy(df):
    orig_index = df.index.names
    out = df.reset_index().drop_duplicates()
    out = out.sort_values(list(out.columns))
    return out.set_index(orig_index)
