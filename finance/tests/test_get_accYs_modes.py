# myfin/finance/tests/test_get_accYs_modes.py

from finance.load_new_txs.get_accYs_modes import get_accYs_modes

from finance.tests.make_test_constructs import make_dbs_from_master_xlsx
from finance.tests.db_compare import db_compare
from finance.tests.test_helpers import print_title

MASTER_XLSX_PATH = ('~/shared/projects/myfin/testing/xlsx_masters/'
                    'get_accYs_master.xlsx')

def test_get_accYs_modes():

    print_title('get_accYs_modes()', borders=False, attrs=['bold'],
                                          color='magenta', char='-')

    dbs = make_dbs_from_master_xlsx(MASTER_XLSX_PATH)

    new_txs_df = dbs['input']['new_txs']
    tx_db = dbs['input']['tx_db']
    cat_db = dbs['input']['cat_db']

    target = dbs['target']['new_txs']

    accYs, modes = get_accYs_modes(new_txs_df['_item'], 'acc1', tx_db, cat_db)

    test = new_txs_df.copy()
    test['accY'] = accYs
    test['mode'] = modes

    db_compare(test, target)
