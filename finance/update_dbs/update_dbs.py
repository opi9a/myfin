import pandas as pd
import os
from pathlib import Path    
import copy

from finance.load_new_txs import archive_dbs, load_dbs_from_disk

from .update_after_changed_unknowns import update_after_changed_unknowns
from .update_after_changed_fuzzy import update_after_changed_fuzzy

"""Functions for updating databases after manual curation of 
unknowns.csv and fuzzy.csv

TODO - ensure don't overwrite anything manually entered in tx_db.  
This may entail implementing and using a 'manual' flag in tx_db['mode']
"""


def update_dbs_after_changes(changed_db_name, acc_path=None, dbs=None,
                             return_dbs=False, write_out_dbs=True):
    """
    Calls update function for a changed_db_name
        - either 'fuzzy_db' or 'unknowns_db'

    Note the update functions will update all affected dbs

    Designed to avoid conflicts of dbs in memory by ensuring updates
    are made to and from disk (i.e. don't implement both fuzzy_db and
    unknowns_db changes on dbs in memory).

    """
    # protection from overwriting disk when testing
    # - pass acc_path when using for real
    # also make a copy if passing from memory, to avoid overwriting
    if dbs is not None:
        write_out_dbs=False
        dbs = copy.deepcopy(dbs)

    # load dbs from disk, if not passed already
    if dbs is None:
        if acc_path is not None:
            acc_path = Path(acc_path)
            dbs = load_dbs(acc_path)
        else:
            print('need either an acc_path or dict of dbs')
            return 1

    SUM_OF_DB_LENS = sum([len(dbs[x]) for x in dbs])

    if changed_db_name == 'unknowns_db':
        dbs = update_after_changed_unknowns(dbs)

    if changed_db_name == 'fuzzy_db':
        dbs = update_after_changed_fuzzy(dbs)

    assert SUM_OF_DB_LENS == sum([len(dbs[x]) for x in dbs])

    if write_out_dbs:
        write_out_dbs(dbs, acc_path, annotation='updated_unknowns_db')

    if return_dbs:
        return dbs




