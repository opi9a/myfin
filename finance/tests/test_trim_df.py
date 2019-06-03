# myfin/finance/tests/test_trim_df.py

from pathlib import Path


from finance.load_new_txs.trim_df import trim_df

from .test_helpers import (db_compare,
                           make_dfs_from_master_xls,
                           make_dbs_from_master_dfs,
                           print_title,
                           make_acc_objects)

MASTER_XLSX_PATH = ('~/shared/projects/myfin/testing/xlsx_masters/'
                    'trim_df_master1.xlsx')


def test_trim_df(master_xlsx_path=MASTER_XLSX_PATH, assertion=False):
    """
    Uses dfs derived from a master xlsx to test the trim_df function.
    """

    print_title('Testing trim_df()')
    print('\nMaking dbs from xls master at', master_xlsx_path)
    raw_dfs = make_dfs_from_master_xls(master_xlsx_path)
    dbs = make_dbs_from_master_dfs(raw_dfs)

    tx_db = dbs['input']['tx_db']
    new_txs_df = dbs['input']['new_txs_df']
    target = dbs['target']['new_txs_df']
    target = target.set_index('date')

    trimmed = trim_df(new_txs_df, tx_db)

    print('\nComparing trimmed df with target', master_xlsx_path)
    db_compare(trimmed, target, index_cols=['date', 'accX', '_item'])
