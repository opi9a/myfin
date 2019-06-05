# myfin/finance/update_dbs/update_after_changed_fuzzy.py

import pandas as pd

from .get_tuples_to_change import get_tuples_to_change
from .get_db_by_tuple import get_db_by_tuple

from .overwrite_tx_db import overwrite_tx_db
from .append_to_db import append_to_db
from .delete_from_db import delete_from_db

def update_after_changed_fuzzy(dbs):
    """
    Implements changes to fuzzy_db, applying them to other dbs as appropriate.

    Returns an updated dict of dbs

      - rows to exit:
        - any with status == 'rejected'
          - for these rows, also:
              - update tx_db with 'unknown' accY
              - add to unknowns_db
        - any with status == 'confirmed'
          - for these rows, also:
              - add the row with new accY to cat_db
      - rows to enter:
          - None
    """


    #-------------------- STATUS == 'REJECTED' -------------------#

    # - overwrite tx_db rows with 'unknown'
    # - append to unknowns_db
    # - delete from dbs['fuzzy_db']

    # get the tuples to change
    def f(x): return x == 'rejected'
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # get the new values to write in
    new_vals = ['unknown'] * len(tuples_to_change)

    # write values to the rows using overwrite_tx_db() accessor
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change, new_vals)
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change,
                                   'rejected fuzzy', col_to_change='mode')

    # append to unknowns_db and reset index for writing out
    dbs['unknowns_db']= append_to_db(dbs['unknowns_db'],
                                         tuples_to_change, new_vals)

    # delete from dbs['fuzzy_db'] and reset index for writing out
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)


    #-------------------- STATUS == 'CONFIRMED' -------------------#

    # - append to cat_db
    # - delete from dbs['fuzzy_db']

    # get the tuples to change
    def f(x): return x == 'confirmed'
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # append to cat_db
    new_vals = get_db_by_tuple(dbs['fuzzy_db']).loc[tuples_to_change, 'accY']
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from dbs['fuzzy_db'] and reset index for writing out
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)

    # overwrite mode in tx_db
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change,
                                   'confirmed fuzzy', col_to_change='mode')
    #-------------------- STATUS == <OTHER> -------------------#
    # changed fuzzy assignment.  status is the new accY
    # overwrite tx_db with the new accY
    # append it to cat_db
    # delete from fuzzy_db
    
    # get the tuples to change
    def f(x): return x not in ['rejected', 'confirmed', pd.np.nan]
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # get the new values to write in
    new_vals = get_db_by_tuple(dbs['fuzzy_db']).loc[tuples_to_change, 'status']

    # overwrite tx_db with the new accY
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change, new_vals)
    dbs['tx_db'] = overwrite_tx_db(dbs['tx_db'], tuples_to_change,
                                   'overwritten fuzzy', col_to_change='mode')

    # append it to cat_db
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from fuzzy_db
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)

    return dbs


