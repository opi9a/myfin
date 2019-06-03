# myfin/finance/tests/test_load_txs.py

from pathlib import Path
from shutil import rmtree
import pandas as pd
import json


from finance.load_new_txs import load_dbs_from_disk
from finance.load_new_txs.load_new_txs import load_new_txs

# local imports
from .test_helpers import (db_compare,
                           make_dfs_from_master_xls,
                           make_dbs_from_master_dfs,
                           print_db_dicts,
                           make_acc_objects,
                           print_title)

from .make_test_project import make_test_project
from .constants import TESTING_DIR, MASTER_XLSX_PATH

TEST_PROJ_DIR = TESTING_DIR / 'test_dir/test_proj'


def test_load_new_txs(master_xlsx_path=MASTER_XLSX_PATH,
                      test_dir=Path('test_dir/test_proj'),
                      return_dbs=False,
                      show_dbs=False,
                      cols_to_ignore=['id', 'source', 'mode'],
                      assertion=False):

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M%S")
    if test_dir is None:
        test_dir = Path('test_dir/') / ts

    if test_dir.exists():
        print('removing existing test_dir', test_dir)
        rmtree(test_dir)

    dbs = make_test_project(master_xlsx_path, test_dir, return_dbs=True)

    # run load_new for each account, saving results to disk
    for acc_path in (test_dir / 'tx_accounts').iterdir():
        load_new_txs(acc_path=acc_path, write_out_dbs=True, move_new_txs=False)

    # load from disk, creating a third element of dbs dict
    dbs['test'] = load_dbs_from_disk(test_dir)

    # just print the dbs optionally
    if show_dbs:
        print_title('printing actual dbs'.upper(), attrs=['bold'])
        print_db_dicts(dbs)
        print()
        
    # list to hold boolean results of db_compare
    results = []

    # get results of db_compare
    print_title('db compare'.upper(), attrs=['bold'])
    for db in dbs['test']:
        results.append(db_compare(dbs['test'][db], dbs['target'][db],
                                  db_name=db, cols_to_ignore=cols_to_ignore,
                                  assertion=assertion))

    if return_dbs:
        return dbs

    else:
        return all(results)



def old_test_load_new_txs(master_xlsx_path=MASTER_XLSX_PATH,
                          test_dir=TEST_PROJ_DIR,
                          return_dbs=False,
                          show_dbs=False,
                          ignore_cols= ['id', 'source', 'mode'],
                          assertion=False):
    """
    Main test sequence for loading new transactions with load_new().

    Calls make_test_project() to generate a test project structure from 
    master_xlsx_path, and return test dbs in memory.

    Note will overwrite each time.  To get a fresh one, pass test_dir=None, and
    a directory will be made based on timestamp which won't be overwritten.

    Runs load_new() for each account, writing results to disk.
    Assesses results using db_compare, with options to actually test
    assertions, and to ignore certain columns (eg 'source') when testing for
    strict equality.

    Returns True if all tests in df_compare satisfied, or optionally returns a
    dict of dbs for each of 'input', 'target' and 'test', each having the set
    of dbs ['tx_db', 'fuzzy_db', 'cat_db', 'unknowns_db'].
    """

    test_dir = Path(test_dir).expanduser()

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M%S")
    if test_dir is None:
        test_dir = Path('test_dir/') / ts

    dbs = make_test_project(master_xlsx_path, test_dir)
        
    # list to hold boolean results of db_compare
    results = []

    # run load_new for each account, saving results to disk
    for acc in accounts:
        print('calling', acc)
        load_new(main_dir=test_dir,
                 acc_name=acc,
                 write_out_dbs=True,
                 move_new_txs=True)

    # load from disk, creating a third element of dbs dict
    dbs['test'] = load_dbs_from_disk(test_dir)

    # get results of db_compare
    print_title('db compare'.upper(), attrs=['bold'])
    for db in dbs['test']:
        results.append(db_compare(dbs['test'][db], dbs['target'][db],
                                  db_name=db, ignore_cols=ignore_cols,
                                  assertion=assertion))
    if return_dbs:
        return dbs

    else:
        return all(results)

