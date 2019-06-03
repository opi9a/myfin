# myfin/finance/update_dbs/delete_from_db.py

from .get_db_by_tuple import get_db_by_tuple

def delete_from_db(db, tuples_to_delete):
    """
    Deletes specified rows from db, returns db
    """

    initial_index = db.index.name

    by_tup = get_db_by_tuple(db)
    by_tup = by_tup.drop(tuples_to_delete)

    return by_tup.reset_index().set_index(initial_index)



