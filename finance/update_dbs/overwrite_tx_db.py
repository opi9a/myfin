# myfin/finance/update_dbs/overwrite_tx_db.py

import pandas as pd

from .get_db_by_tuple import get_db_by_tuple


def overwrite_tx_db(tx_db, tuples_to_change, new_vals, col_to_change='accY', 
                    overwrite_manual=False):
    """
    Pass an iterable of '_item', 'accX' tuples_to_change, and an
    iterable of corresponding new_vals.

    Change the corresponding entries in tx_db excluding those with
    'mode' == 'manual'
    """

    if isinstance(new_vals, str):
        new_vals = [new_vals] * len(list(tuples_to_change))

    tx_db_by_tup = get_db_by_tuple(tx_db)

    # select those to change, excluding those with 'manual' mode
    mask = tx_db_by_tup.index.isin(tuples_to_change)
    
    if not overwrite_manual:
        mask = mask & (tx_db_by_tup['mode'] != 'manual').values

    # split the db, work on one bit and re-append
    #  (avoids SettingWithCopy warning)
    tx_db_to_change = tx_db_by_tup[mask].copy()
    tx_db_remainder = tx_db_by_tup[~mask]

    # iterate over the lists of tuples and new_vals
    for tup, new_val in zip(tuples_to_change, new_vals):

        if tup in tx_db_to_change.index:
            tx_db_to_change.loc[tup, col_to_change] = new_val

    # put tx_db back together again
    tx_db_by_tup = pd.concat([tx_db_remainder, tx_db_to_change])

    return tx_db_by_tup.reset_index().set_index('date')


