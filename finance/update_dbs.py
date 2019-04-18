import pandas as pd
import os

"""Functions for updating databases after manual curation of 
unknowns.csv and fuzzy.csv

TODO - ensure don't overwrite anything manually entered in tx_db.  
This may entail implementing and using a 'manual' flag in tx_db['mode']
"""


def update_all_dbs(paths_dict, return_dbs=False, write_out_dbs=True):
    """
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

    tx_db       = pd.read_csv(paths_dict['tx_db'], index_col='date')
    unknowns_db = pd.read_csv(paths_dict['unknowns_db'], index_col='_item')
    cat_db      = pd.read_csv(paths_dict['cat_db'], index_col='_item')
    fuzzy_db    = pd.read_csv(paths_dict['fuzzy_db'], index_col='_item')

    tx_by_tup = (tx_db.copy().reset_index()
                             .set_index(['_item', 'accX']).sort_index())
    un_by_tup = unknowns_db.copy().reset_index().set_index(['_item', 'accX'])
    fz_by_tup = fuzzy_db.copy().reset_index().set_index(['_item', 'accX'])
    ca_by_tup = cat_db.copy().reset_index().set_index(['_item', 'accX'])
    
    SUM_OF_DB_LENS = sum([len(x) for x in [unknowns_db, cat_db, fuzzy_db]])

    # unknowns: any accY != unknown:
    # - overwrite tx_db rows
    # - append to cat_db
    # - delete from unknowns

    # overwrite tx_db
    tuples_to_change = un_by_tup.index[un_by_tup['accY'] != 'unknown']

    # get tx_db rows - NB exclude 'mode'='manual'
    mask = ((tx_by_tup.index.isin(tuples_to_change)) &
            (tx_by_tup['mode'] != 'manual'))

    rows_to_change = tx_by_tup.loc[mask]
    new_vals = (pd.Series(tuple(rows_to_change.index))
                .apply(lambda x: un_by_tup.loc[x]))

    tx_by_tup.loc[tx_by_tup.index.isin(tuples_to_change),
                  'accY'] = new_vals.values
    tx_db = tx_by_tup.reset_index().set_index('date')

    # append to cat_db
    ca_by_tup = ca_by_tup.append(un_by_tup[un_by_tup['accY'] != 'unknown'])
    cat_db = ca_by_tup.reset_index().set_index('_item')
    cat_db = cat_db.drop_duplicates()

    # delete from unknowns
    un_by_tup = un_by_tup.drop(tuples_to_change)
    unknowns_db = un_by_tup.reset_index().set_index('_item')

    # fuzzys: status=='rejected':
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

    # append to unknowns_db
    appendee = pd.DataFrame(index=tuples_to_change)
    appendee['accY'] = 'unknown'
    un_by_tup = un_by_tup.append(appendee)
    un_by_tup = un_by_tup.reset_index().drop_duplicates()
    unknowns_db = un_by_tup.set_index('_item')

    # delete from fuzzy_db
    fz_by_tup = fz_by_tup.drop(tuples_to_change)
    fuzzy_db = fz_by_tup.reset_index().set_index('_item')

    # fuzzys: status=='confirmed':
    # - append to cat_db
    # - delete from fuzzy_db

    # get the tuples to change
    tuples_to_change = fz_by_tup.index[fz_by_tup['status'] == 'confirmed']

    # append to cat_db
    appendee = pd.DataFrame(fz_by_tup.loc[tuples_to_change, 'accY'])
    ca_by_tup = ca_by_tup.append([appendee])
    cat_db = ca_by_tup.reset_index().drop_duplicates()
    cat_db = cat_db.set_index('_item')

    # delete from fuzzy_db
    fz_by_tup = fz_by_tup.drop(tuples_to_change)
    fuzzy_db = fz_by_tup.reset_index().set_index('_item')

    # assert no change in number of entries
    assert SUM_OF_DB_LENS == sum([len(x) for x in [unknowns_db, cat_db, fuzzy_db]])

    if write_out_dbs:
        tx_db.to_csv(tx_db_path)
        unknowns_db.to_csv(unknowns_db_path)
        cat_db.to_csv(cat_db_path)
        fuzzy_db.to_csv(fuzzy_db_path)

    if return_dbs:
        return dict(tx_db=tx_db, cat_db=cat_db,
                    unknowns_db=unknowns_db, fuzzy_db=fuzzy_db)


# ----------------------------------------------------------------------------

def update_fuzzy(account, fuzzy_db_path='fuzzy_db.csv', tx_db_path='tx_db.csv',
                 unknowns_db_path='unknowns_db.csv', cat_db_path='cat_db.csv',
                 return_txdb=False):
    """Take a csv file of fuzzy matches for which some have status
    set to 'confirmed', some 'rejected', some 'modified',
    (others left 'unconfirmed').

    For those that are confirmed:
        - add to cat_db
        - delete from fuzzy

    For those that are modified:
        - add to cat_db
        - edit in tx_db
        - delete from fuzzy

    For those that are rejected:
        - add to unknown
        - delete from fuzzy

    For those that remain unconfirmed:
        - leave in fuzzy (i.e. write only these, to disk)
    """
    fuzzy_db = pd.read_csv(fuzzy_db_path, index_col='_item')
    cat_db = pd.read_csv(cat_db_path, index_col='_item')
    unknowns_db = pd.read_csv(unknowns_db_path, index_col='_item')
    tx_db = pd.read_csv(tx_db_path)

    confirmed = fuzzy_db.loc[fuzzy_db['status'] == 'confirmed'].drop('status',
                                                                     axis=1)
    cat_db = pd.concat([cat_db, confirmed])
    cat_db.to_csv(cat_db_path)

    rejected = fuzzy_db.loc[fuzzy_db['status'] == 'rejected'].drop('status',
                                                                   axis=1)
    rejected['accY'] = 'unknown'
    unknowns_db = pd.concat([unknowns_db, rejected])
    unknowns_db.to_csv(unknowns_db_path)

    modified = fuzzy_db.loc[fuzzy_db['status'] == 'modified'].drop('status',
                                                                   axis=1)
    cat_db = pd.concat([cat_db, modified])
    cat_db.to_csv(cat_db_path)

    # call edit_tx to overwrite in tx_db
    modified = fuzzy_db.loc[fuzzy_db['status'] == 'modified']
    for tx in modified.index:
        new_val = modified.loc[tx, 'accY']
        edit_tx(tx_db, 'accY', new_val,
                [tx_db['_item'] == tx,
                 tx_db['accX'] == account])

    tx_db = tx_db.reset_index()
    tx_db = (tx_db[['date', 'accX', 'accY', 'net_amt', 'ITEM', '_item',
                   'id', 'mode']].set_index('date'))

    tx_db.to_csv(tx_db_path)

    # save back only those still unconfirmed
    fuzzy_db.loc[fuzzy_db['status'] == 'unconfirmed'].to_csv(fuzzy_db_path)

    if return_txdb:
        return tx_db


# -----------------------------------------------------------------------------

def update_unknowns(account, unknowns_path='unknowns_db.csv',
                    cat_db_path='cat_db.csv', tx_db_path='tx_db.csv',
                    return_txdb=False):

    """Take a csv file of unknowns for which some have had accY
    categories manually completed (i.e. 'accY'!='unknown').

    For those that are completed:
        - update the relevant fields in a tx_db.
        - add to cat_db
        - delete from unknowns
    """

    tx_db = pd.read_csv(tx_db_path, index_col='date')

    unknowns = pd.read_csv(unknowns_path, index_col='_item')

    if account not in unknowns['accX'].values:
        print("WARNING: that account name has not been found in unknowns_db")

    to_edit = unknowns.loc[unknowns['accY'] != 'unknown']

    if len(to_edit) == 0:
        print('no updated unknowns to process')
        return

    cat_db = pd.read_csv(cat_db_path, index_col='_item')

    base_masklist = [tx_db['accX'] == account,
                     tx_db['accY'] == 'unknown']

    for tx in to_edit.index:
        # first the tx_db
        masks = base_masklist + [tx_db['_item'] == tx]
        new_val = to_edit.loc[tx, 'accY']
        edit_tx(df=tx_db, target_col='accY', new_val=new_val, masks=masks)

        # now the cat_db
        cat_db.loc[tx] = [account, new_val]

    # save back only those still unknown
    unknowns.loc[unknowns['accY'] == 'unknown'].to_csv(unknowns_path)

    tx_db.to_csv(tx_db_path)
    cat_db.to_csv(cat_db_path)

    update_persistent_cat_db()

    if return_txdb:
        return tx_db


# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------

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
