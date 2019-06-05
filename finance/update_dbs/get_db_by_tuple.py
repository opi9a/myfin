# myfin/finance/update_dbs/get_db_by_tuple.py

def get_db_by_tuple(db, index_labels=None):
    """
    Returns a db with ('_item', 'accX') tuples as index

    Can optionally use other labels
    """

    if index_labels is None:
        index_labels = ['_item', 'accX']

    return (db#.copy()
              .reset_index()
              .set_index(index_labels)
              .sort_index())
