# myfin/testing/test_all.py

from .test_load_txs import test_load_new_txs
from .test_update_dbs import test_all_update

def test_all():
    """
    Just a script that calls all known tests
    """

    test_all_update()
    test_load_new_txs()
