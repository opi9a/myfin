# myfin/finance/update_dbs/get_db_by_tuple.py

def get_db_by_tuple(db):
    """
    Returns a db with ('_item', 'accX') tuples as index
    """

    return (db#.copy()
              .reset_index()
              .set_index(['_item', 'accX'])
              .sort_index())
