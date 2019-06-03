# myfin/finance/update_dbs/append_to_db.py

import pandas as pd
from .get_db_by_tuple import get_db_by_tuple


def append_to_db(db, tuples_to_append, new_vals, column='accY'):
    """
    Makes a df based on the passed tuples_to_append ('_item', 'accX')
    and new_vals, with name of passed column, and appends to the passed db
    """

    initial_index = db.index.name

    if isinstance(new_vals, str) and len(tuples_to_append) > 1:
        print('expanding new_vals')
        new_vals = [new_vals] * len(tuples_to_append)

    by_tup = get_db_by_tuple(db)
    appendee = pd.DataFrame({column: new_vals}, index=tuples_to_append)
    
    by_tup = by_tup.append([appendee])

    return by_tup.reset_index().set_index(initial_index)

