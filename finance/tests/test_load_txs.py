# myfin/finance/tests/test_load_txs.py

from pathlib import Path
from shutil import rmtree
import pandas as pd
import json


from finance.helpers.load_dbs_from_disk import load_dbs_from_disk
from finance.load_new_txs.load_new_txs import load_new_txs

# local imports
from .db_compare import db_compare
from .test_helpers import print_db_dicts, print_title
from .make_test_project import make_test_project
from .constants import TESTING_DIR, MASTER_XLSX_PATH

TEST_PROJ_DIR = TESTING_DIR / 'test_dir/test_proj'


def test_load_new_txs(master_xlsx_path=MASTER_XLSX_PATH,
                      test_dir=Path('test_dir/test_proj'),
                      return_dbs=False,
                      cols_to_ignore=['id', 'source'],
                      assertion=False):

    print_title('load_new_txs()', borders=True, attrs=['bold'],
                                      color='magenta', char='-')

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M%S")
    if test_dir is None:
        test_dir = Path('test_dir/') / ts

    if test_dir.exists():
        print('removing existing test_dir', test_dir)
        rmtree(test_dir)

    dbs = make_test_project(master_xlsx_path, test_dir, return_dbs=True)

    # run load_new for each account, saving results to disk
    for acc_path in (test_dir / 'tx_accounts').iterdir():
        load_new_txs(acc_path=acc_path, write_out_tx_db=True, move_new_txs=False)

    # load from disk, creating a third element of dbs dict
    dbs['test'] = load_dbs_from_disk(test_dir)

    # list to hold boolean results of db_compare
    results = []

    # get results of db_compare
    for db in dbs['test']:
        results.append(db_compare(dbs['test'][db], dbs['target'][db],
                                  db_name=db, cols_to_ignore=cols_to_ignore,
                                  assertion=assertion))
    if return_dbs:
        return dbs

    else:
        return all(results)

