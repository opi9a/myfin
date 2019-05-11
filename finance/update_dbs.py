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
    # make versions 'by tuple', to allow indexing required for overwriting etc
    by_tup = {db: get_dbs_by_tuple(dbs[db]) for db in dbs}


    #-------------------- STATUS == 'REJECTED' -------------------#

    # - overwrite tx_db rows with 'unknown'
    # - append to unknowns_db
    # - delete from dbs['fuzzy_db']

    # get the tuples to change
    mask = by_tup['fuzzy_db']['status'] == 'rejected'
    tuples_to_change = by_tup['fuzzy_db'].index[mask]

    # overwrite tx_db rows with 'unknown' - NB exclude 'mode'='manual'
    mask = ((by_tup['tx_db'].index.isin(tuples_to_change)) &
            (by_tup['tx_db']['mode'] != 'manual'))

    by_tup['tx_db'].loc[mask, 'accY'] = 'unknown'
    dbs['tx_db'] = by_tup['tx_db'].reset_index().set_index('date')

    # append to dbs['unknowns_db']and reset index for writing out
    appendee = pd.DataFrame(index=tuples_to_change)
    appendee['accY'] = 'unknown'
    by_tup['unknowns_db'] = by_tup['unknowns_db'].append(appendee)
    by_tup['unknowns_db'] = by_tup['unknowns_db'].reset_index().drop_duplicates()
    dbs['unknowns_db']= by_tup['unknowns_db'].set_index('_item')

    # delete from dbs['fuzzy_db'] and reset index for writing out
    by_tup['fuzzy_db'] = by_tup['fuzzy_db'].drop(tuples_to_change)
    dbs['fuzzy_db'] = by_tup['fuzzy_db'].reset_index().set_index('_item')


    #-------------------- STATUS == 'CONFIRMED' -------------------#

    # - append to cat_db
    # - delete from dbs['fuzzy_db']

    # get the tuples to change
    mask = by_tup['fuzzy_db']['status'] == 'confirmed'
    tuples_to_change = by_tup['fuzzy_db'].index[mask]

    # append to cat_db
    appendee = pd.DataFrame(by_tup['fuzzy_db'].loc[tuples_to_change, 'accY'])

    print('appendee out\n', appendee)
    by_tup['cat_db'] = by_tup['cat_db'].append([appendee])
    dbs['cat_db'] = by_tup['cat_db'].reset_index().drop_duplicates()
    dbs['cat_db'] = dbs['cat_db'].set_index('_item')

    # delete from dbs['fuzzy_db'] and reset index for writing out
    by_tup['fuzzy_db'] = by_tup['fuzzy_db'].drop(tuples_to_change)
    dbs['fuzzy_db'] = by_tup['fuzzy_db'].reset_index().set_index('_item')

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

    # make versions 'by tuple', to allow indexing required for overwriting etc
    by_tup = {db: get_dbs_by_tuple(dbs[db]) for db in dbs}

    # overwrite tx_db
    # - first get the tuples (index) that need to be changed
    # - that is, unknowns_db rows where accY is NOT unknown
    mask = by_tup['unknowns_db']['accY'] != 'unknown'
    tuples_to_change = (by_tup['unknowns_db'].index[mask])

    # now get the corresponding rows from tx_db rows to change
    # - NB exclude 'mode'='manual'
    mask = ((by_tup['tx_db'].index.isin(tuples_to_change)) &
            (by_tup['tx_db']['mode'] != 'manual'))

    rows_to_change = by_tup['tx_db'].loc[mask]

    # get the new values to write in
    new_vals = (pd.Series(tuple(rows_to_change.index))
                .apply(lambda x: by_tup['unknowns_db'].loc[x]))

    # write values to the rows
    by_tup['tx_db'].loc[by_tup['tx_db'].index.isin(tuples_to_change),
                  'accY'] = new_vals.values
    dbs['tx_db'] = by_tup['tx_db'].reset_index().set_index('date')

    # append to cat_db and reset index for writing out
    mask = by_tup['unknowns_db']['accY'] != 'unknown'
    by_tup['cat_db'] = by_tup['cat_db'].append(by_tup['unknowns_db'][mask])
    dbs['cat_db'] = by_tup['cat_db'].reset_index().set_index('_item')
    dbs['cat_db'] = dbs['cat_db'].drop_duplicates()

    # delete from unknowns and reset index for writing out
    by_tup['unknowns_db'] = by_tup['unknowns_db'].drop(tuples_to_change)
    dbs['unknowns_db'] = by_tup['unknowns_db'].reset_index().set_index('_item')

    return dbs



#-------------------------- HELPERS  -------------------------- 

def get_dbs_by_tuple(df):
    """
    Returns a copy of a db with ('_item', 'accX') tuples as index
    """

    return (df.copy()
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

def update_all_dbs(acc_path=None, dbs=None, return_dbs=False, write_out_dbs=True):
    """
    OBSOLETE - replaced with update_dbs, which calls individual functions to
    make updates based on changes in EITHER fuzzy_db or unknowns_db

    Scan unknowns_db and fuzzy_db for changes.  Amend these and cat_db, tx_db
    as reqd.

    Functionality as follows:

        unknowns_db:
          - rows to exit:
            - any that have an accY assigned (i.e. not 'unknown')
              - for these rows, also:
                  - update tx_db with the new accY
                  - add the row with new accY to cat_db
          - rows to enter:
              - rejects from fuzzy_db, with accY = unknown
          
        fuzzy_db:
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
              
        cat_db:
          - rows to exit:
            - None
          - rows to enter:
            - confirmed from fuzzy_db
            - knowns from unknowns_db
    """

    if acc_path is None and dbs is None:
        print('need either an acc_path or dict of dbs')
        return 1

    # load dbs if reqd, assign to variable names
    if dbs is None:
        acc_path = Path(acc_path)
        dbs = load_dbs(acc_path)

    tx_db       = dbs['tx_db']
    unknowns_db = dbs['unknowns_db']
    cat_db      = dbs['cat_db']
    fuzzy_db    = dbs['fuzzy_db']

    SUM_OF_DB_LENS = sum([len(x) for x in [unknowns_db, cat_db, fuzzy_db]])

    # make versions 'by tuple', to allow indexing required for overwriting etc
    tx_by_tup = (tx_db.copy().reset_index()
                             .set_index(['_item', 'accX']).sort_index())
    un_by_tup = unknowns_db.copy().reset_index().set_index(['_item', 'accX'])
    fz_by_tup = fuzzy_db.copy().reset_index().set_index(['_item', 'accX'])
    ca_by_tup = cat_db.copy().reset_index().set_index(['_item', 'accX'])
    
    dbs_by_tup = {}
    for db in dbs:
        dbs_by_tup[db] = (dbs[db].copy()
                                 .reset_index()
                                 .set_index(['_item', 'accX'])
                                 .sort_index())


    ########################## UNKNOWNS #########################
    # any accY != unknown:
    # - overwrite tx_db rows
    # - append to cat_db
    # - delete from unknowns

    # overwrite tx_db
    tuples_to_change = un_by_tup.index[un_by_tup['accY'] != 'unknown']

    # get tx_db rows to change - NB exclude 'mode'='manual'
    mask = ((tx_by_tup.index.isin(tuples_to_change)) &
            (tx_by_tup['mode'] != 'manual'))

    rows_to_change = tx_by_tup.loc[mask]

    # get the new values to write in
    new_vals = (pd.Series(tuple(rows_to_change.index))
                .apply(lambda x: un_by_tup.loc[x]))

    # write values to the rows
    tx_by_tup.loc[tx_by_tup.index.isin(tuples_to_change),
                  'accY'] = new_vals.values
    tx_db = tx_by_tup.reset_index().set_index('date')

    # append to cat_db and reset index for writing out
    ca_by_tup = ca_by_tup.append(un_by_tup[un_by_tup['accY'] != 'unknown'])
    cat_db = ca_by_tup.reset_index().set_index('_item')
    cat_db = cat_db.drop_duplicates()

    # delete from unknowns and reset index for writing out
    un_by_tup = un_by_tup.drop(tuples_to_change)
    unknowns_db = un_by_tup.reset_index().set_index('_item')

    ############################ FUZZY ############################

    #-------------------- STATUS == 'REJECTED' -------------------#

    # - overwrite tx_db rows with 'unknown'
    # - append to unknowns_db
    # - delete from fuzzy_db

    # get the tuples to change
    tuples_to_change = fz_by_tup.index[fz_by_tup['status'] == 'rejected']

    # overwrite tx_db rows with 'unknown' - NB exclude 'mode'='manual'
    mask = ((tx_by_tup.index.isin(tuples_to_change)) &
            (tx_by_tup['mode'] != 'manual'))

    tx_by_tup.loc[mask, 'accY'] = 'unknown'
    tx_db = tx_by_tup.reset_index().set_index('date')

    # append to unknowns_db and reset index for writing out
    appendee = pd.DataFrame(index=tuples_to_change)
    appendee['accY'] = 'unknown'
    un_by_tup = un_by_tup.append(appendee)
    un_by_tup = un_by_tup.reset_index().drop_duplicates()
    unknowns_db = un_by_tup.set_index('_item')

    # delete from fuzzy_db and reset index for writing out
    fz_by_tup = fz_by_tup.drop(tuples_to_change)
    fuzzy_db = fz_by_tup.reset_index().set_index('_item')


    #-------------------- STATUS == 'CONFIRMED' -------------------#

    # - append to cat_db
    # - delete from fuzzy_db

    # get the tuples to change
    tuples_to_change = fz_by_tup.index[fz_by_tup['status'] == 'confirmed']

    # append to cat_db
    appendee = pd.DataFrame(fz_by_tup.loc[tuples_to_change, 'accY'])
    print('appendee out (all)\n', appendee)
    ca_by_tup = ca_by_tup.append([appendee])
    cat_db = ca_by_tup.reset_index().drop_duplicates()
    cat_db = cat_db.set_index('_item')

    # delete from fuzzy_db and reset index for writing out
    fz_by_tup = fz_by_tup.drop(tuples_to_change)
    fuzzy_db = fz_by_tup.reset_index().set_index('_item')


    ########################## TIDYING UP ##########################

    # assert no change in number of entries
    # assert SUM_OF_DB_LENS == sum([len(x) for x in [unknowns_db, cat_db, fuzzy_db]])

    if write_out_dbs:
        tx_db.to_csv(acc_path / 'tx_db.csv')
        unknowns_db.to_csv(acc_path / 'unknowns_db.csv')
        cat_db.to_csv(acc_path / 'cat_db.csv')
        fuzzy_db.to_csv(acc_path / 'fuzzy_db.csv')

        archive_dbs(acc_path=acc_path, annotation='update_dbs')

    if return_dbs:
        return dict(tx_db=tx_db, cat_db=cat_db,
                    unknowns_db=unknowns_db, fuzzy_db=fuzzy_db)




def edit_tx(df, target_col, new_val, masks, return_txdb=False):
    """Edits transactions of an input df by selection based on columns

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
