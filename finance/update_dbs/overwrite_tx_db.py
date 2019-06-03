# myfin/finance/update_dbs/overwrite_tx_db.py

from .get_db_by_tuple import get_db_by_tuple

def overwrite_tx_db(tx_db, tuples_to_change, new_vals, col_to_change='accY'):
    """
    Pass an iterable of '_item', 'accX' tuples_to_change, and an
    iterable of corresponding new_vals.

    Change the corresponding entries in tx_db

    TODO: exclude 'manual'
    """
    if isinstance(new_vals, str):
        new_vals = [new_vals] * len(list(tuples_to_change))


    tx_db_by_tup = get_db_by_tuple(tx_db)

    for tuple, new_val in zip(tuples_to_change, new_vals):
        tx_db_by_tup.loc[tuple, col_to_change] = new_val

    return tx_db_by_tup.reset_index().set_index('date')


