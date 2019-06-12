# myfin/testing/test_all.py
"""
Script to call all tests
"""

from .test_load_txs import test_load_new_txs
from .test_trim_df import test_trim_df
from .test_get_accYs_modes import test_get_accYs_modes
from .test_amend_db import test_amend_db

def test_all():
    """
    Just a script that calls all known tests
    """

    test_load_new_txs()
    test_trim_df()
    test_get_accYs_modes()
    test_amend_db()
