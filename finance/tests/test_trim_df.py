# myfin/finance/tests/test_trim_df.py

from pathlib import Path

from finance.load_new_txs.trim_df import trim_df

from .db_compare import db_compare
from .make_test_constructs import make_dbs_from_master_xlsx
from .test_helpers import print_title

MASTER_XLSX_PATH = ('~/shared/projects/myfin/testing/xlsx_masters/'
                    'trim_df_master.xlsx')


def test_trim_df(master_xlsx_path=MASTER_XLSX_PATH, assertion=False,
                 compare_dbs=True, show_even_if_equal=False, return_dbs=False):
    """
    Uses dfs derived from a master xlsx to test the trim_df function.
    """

    print_title('Testing trim_df()')
    print('\nMaking dbs from xls master at', master_xlsx_path)
    dbs = make_dbs_from_master_xlsx(master_xlsx_path)

    tx_db = dbs['input']['tx_db']
    new_txs_df = dbs['input']['new_txs_df']
    target = dbs['target']['new_txs_df']
    target = target.set_index('date')

    trimmed = trim_df(new_txs_df, tx_db)

    if compare_dbs:
        print('\nComparing trimmed df with target', master_xlsx_path)
        db_compare(trimmed, target, index_cols=['date', 'accX', '_item'],
                   show_even_if_equal=show_even_if_equal)

    if return_dbs:
        return {'new_txs_df': new_txs_df,
                'tx_db': tx_db,
                'trimmed': trimmed}
