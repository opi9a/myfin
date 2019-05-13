import pandas as pd
import os
from pathlib import Path    

from finance.load_new_txs import archive_dbs, load_dbs

"""Functions for updating databases after manual curation of 
unknowns.csv and fuzzy.csv

TODO - ensure don't overwrite anything manually entered in tx_db.  
This may entail implementing and using a 'manual' flag in tx_db['mode']
"""


def update_dbs(changed_db_name, acc_path=None, dbs=None,
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
    if dbs is not None:
        write_out_dbs=False

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
    f = lambda x: x == 'rejected'
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # get the new values to write in
    new_vals = ['unknown'] * len(tuples_to_change)

    # write values to the rows using update_tx_db() accessor
    dbs['tx_db'] = update_tx_db(dbs['tx_db'], tuples_to_change, new_vals)

    # append to unknowns_db and reset index for writing out
    dbs['unknowns_db']= append_to_db(dbs['unknowns_db'],
                                         tuples_to_change, new_vals)

    # delete from dbs['fuzzy_db'] and reset index for writing out
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)


    #-------------------- STATUS == 'CONFIRMED' -------------------#

    # - append to cat_db
    # - delete from dbs['fuzzy_db']

    # get the tuples to change
    f = lambda x: x == 'confirmed'
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # append to cat_db
    new_vals = get_db_by_tuple(dbs['fuzzy_db']).loc[tuples_to_change, 'accY']
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from dbs['fuzzy_db'] and reset index for writing out
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)

    #-------------------- STATUS == <OTHER> -------------------#
    # changed fuzzy assignment.  status is the new accY
    # overwrite tx_db with the new accY
    # appendt it to cat_db
    # delete from fuzzy_db
    
    # get the tuples to change
    f = lambda x: x not in ['rejected', 'confirmed', pd.np.nan]
    col = 'status'
    tuples_to_change = get_tuples_to_change(dbs['fuzzy_db'], col, f)

    # get the new values to write in
    new_vals = get_db_by_tuple(dbs['fuzzy_db']).loc[tuples_to_change, 'status']

    # overwrite tx_db with the new accY
    dbs['tx_db'] = update_tx_db(dbs['tx_db'], tuples_to_change, new_vals)

    # append it to cat_db
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from fuzzy_db
    dbs['fuzzy_db'] = delete_from_db(dbs['fuzzy_db'], tuples_to_change)

    return dbs


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

    # write values to the rows using update_tx_db() accessor
    dbs['tx_db'] = update_tx_db(dbs['tx_db'], tuples_to_change, new_vals)

    # append to cat_db and reset index for writing out
    dbs['cat_db'] = append_to_db(dbs['cat_db'], tuples_to_change, new_vals)

    # delete from unknowns and reset index for writing out
    dbs['unknowns_db'] = delete_from_db(dbs['unknowns_db'], tuples_to_change)

    return dbs



#-------------------------- HELPERS  -------------------------- 

def update_tx_db(tx_db, tuples_to_change, new_vals):
    """
    Pass an iterable of '_item', 'accX' tuples_to_change, and an
    iterable of corresponding new_vals.

    Change the corresponding entries in tx_db

    TODO: exclude 'manual'
    """

    tx_db_by_tup = get_db_by_tuple(tx_db)

    for tuple, new_val in zip(tuples_to_change, new_vals):
        tx_db_by_tup.loc[tuple, 'accY'] = new_val

    return tx_db_by_tup.reset_index().set_index('date')


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


def delete_from_db(db, tuples_to_delete):
    """
    Deletes specified rows from db, returns db
    """

    initial_index = db.index.name

    by_tup = get_db_by_tuple(db)
    by_tup = by_tup.drop(tuples_to_delete)

    return by_tup.reset_index().set_index(initial_index)


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
    

def get_db_by_tuple(db):
    """
    Returns a db with ('_item', 'accX') tuples as index
    """

    return (db#.copy()
              .reset_index()
              .set_index(['_item', 'accX'])
              .sort_index())


def write_out_dbs(dbs, acc_path, archive=True, annotation=None):
    """
    Helper function to write out the dbs in passed dict to appropriate
    files in acc_path.

    Optionally archive them with the passed annotation
    """

    acc_path = Path(acc_path)

    for db in dbs:
        dbs[db].to_csv(acc_path / (db + '.csv'))

    if archive:
        archive_dbs(acc_path=acc_path, annotation=annotation)


#-------------------------- OBSOLETE  -------------------------- 

def edit_tx(df, target_col, new_val, masks, return_txdb=False):
    """
    Edits transactions of an input df by selection based on columns

    target_col  : the column to be edited

    new_val     : the value to be inserted at selected fields

    masks       : a list of boolean df masks to apply to select rows

                - eg [df['ITEM'].str.lower().strip() == 'newt cuffs',
                      df['accY'] == 'groceries',
                      df['amt'] >= 100,
                      df['id'] < 999,
                      df['mode'] == -1,
                      ]

    The passed list of masks is aggregated with successively overlays,
    to give a cumulative mask applied to the df to select rows for editing.
    """

    mask = True

    for m in masks:
        mask = mask & m

    # finally overwrite the selection
    df.loc[mask, target_col] = new_val

    if return_txdb:
        return df


def update_persistent_cat_db(cat_db_path='cat_db.csv',
                             persistent_cat_db_path='../persistent_cat_db.csv',
                             return_updated_db=False):

    if os.path.exists(persistent_cat_db_path):
        persist_db = pd.read_csv(persistent_cat_db_path)
    else:
        print("Cannot find db at\n" + os.path.abspath(persistent_cat_db_path))
        return 1

    cat_db = pd.read_csv(cat_db_path)

    updated = pd.concat([persist_db, cat_db]).drop_duplicates()
    updated.to_csv(persistent_cat_db_path, index=False)

    if return_updated_db:
        return updated_db
