# myfin/finance/update_dbs/update_after_changed_unknowns.py

from .get_tuples_to_change import get_tuples_to_change
from .get_db_by_tuple import get_db_by_tuple

from .overwrite_tx_db import overwrite_tx_db
from .append_to_db import append_to_db
from .delete_from_db import delete_from_db


def update_after_changed_unknowns(dbs):
    """
    Implements changes to unknowns_db, applying them to other dbs as appropriate.

    Returns an updated dict of dbs

      - rows to exit:
        - any that have an accY assigned (i.e. not 'unknown')
          - for these rows, also:
              - update tx_db with the new accY
              - add the row with new accY to cat_db
      - rows to enter:
          - rejects from fuzzy_db, with accY = unknown
    """

    # overwrite tx_db

    # get the tuples to change - unknowns_db rows where accY is NOT unknown
    f = lambda x: x != 'unknown'
    col = 'accY'
    tuples_to_change = get_tuples_to_change(dbs['unknowns_db'], col, f)

    # get the new values to write in
    new_vals = get_db_by_tuple(dbs['unknowns_db']).loc[tuples_to_change, 'accY']

    # write values to the rows using overwrite_tx_db() accessor
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change, new_vals)
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change,
                                   'overwritten unknown', col_to_change='mode')

    # append to cat_db and reset index for writing out
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from unknowns and reset index for writing out
    dbs['unknowns_db'] = delete_from_db(dbs['unknowns_db'], tuples_to_change)

    return dbs

