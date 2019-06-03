# myfin/finance/update_dbs/get_tuples_to_change.py

from .get_db_by_tuple import get_db_by_tuple

def get_tuples_to_change(db, col, f):
    """
    Return an index of ('_item', 'accX') tuples corresponding to the filter
    of f applied to column col of input dataframe db.

    Eg passing col = 'accY', f = lambda x: x == 'target' will yield the
    '_item', 'accX' tuples for txs where accY is 'target'
    """
    by_tup = get_db_by_tuple(db)
    mask = by_tup[col].apply(f)
    return by_tup.index[mask]
    


