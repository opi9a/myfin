import pandas as pd
import numpy as np
import os

from finance.categorise import categorise
from finance.general import consol_debit_credit

def load_new_txs(new_tx_paths, tx_db_path, cat_db_path, unknowns_path, fuzzy_db_path,
                 account_name, parser, return_df=False):

    """Import raw transactions and return a tx_df in standard format,
    with date index, and columns: from, to, amt

    new_tx_paths : a list of csv files with new transactions
    
    tx_db_path:     the path of the existing tx database. 
                   (or a new one to create)

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns

    parser       : dict with instructions for processing the raw tx raw_tx_path
                    - 'input_type' : 'credit_debit' or 'net_amt'
                    - 'date_format': eg "%d/%m/%Y"
                    - 'map'        : dict of map for column labels
                                     (new labels are keys, old are values)

                 - mapping must cover following columns (i.e. new labels):
                   - net_amt: ['date', 'accX', 'accY', 'net_amt', 'ITEM']
                   - credit_debit: 'debit_amt', 'credit_amt' replace 'net_amt'


    """

    # 1. aggregate input csvs to a single df

    date_parser = lambda x: pd.datetime.strptime(x, parser['date_format'])

    new_tx_df = pd.concat([pd.read_csv(f, parse_dates=[parser['map']['date']],
                                          skipinitialspace=True,
                                          date_parser=date_parser,
                                          dayfirst=True)
                           for f in new_tx_paths])


    # 2. organise columns using parser, and add '_item' column
    
    new_tx_df = new_tx_df[list(parser['map'].values())]
    new_tx_df.columns = parser['map'].keys()
    new_tx_df['_item'] = new_tx_df['ITEM'].str.lower().str.strip() 

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        new_tx_df['net_amt'] = (new_tx_df['debit_amt']
                             .subtract(new_tx_df['credit_amt'], fill_value=0))
        

    # 3. load files from RAM
    if os.path.isfile(tx_db_path):
        tx_db = pd.read_csv(tx_db_path, index_col='date')
    else: tx_db = None

    if os.path.isfile(cat_db_path):
        cat_db = pd.read_csv(cat_db_path, index_col='_item')
    else: cat_db = None
  
    if os.path.isfile(unknowns_path):
        unknowns_db = pd.read_csv(unknowns_path, index_col='_item')
    else: unknowns_db = None
  
    if os.path.isfile(fuzzy_db_path):
        fuzzy_db = pd.read_csv(fuzzy_db_path, index_col='ITEM')
    else: fuzzy_db = None

    print('fuzzy_db is', fuzzy_db)
    print('fuzzy_db path is', fuzzy_db_path)
  

    # 4. call categorise() to get accY and mode columns,
    categ_out = categorise(new_tx_df['ITEM'], account=account_name,
                           tx_db=tx_db,
                           cat_db=cat_db,
                           fuzzy_db=fuzzy_db,
                           unknowns_db=unknowns_db)

    new_tx_df['accY'] = [x[0] for x in categ_out]
    new_tx_df['mode'] = [x[1] for x in categ_out]


    # 5. add id and account name columns to make output df
    max_current = int(pd.read_csv(tx_db_path)['id'].max())
    new_tx_df['id'] = np.arange(max_current + 1,
                                max_current + 1 + len(new_tx_df)).astype(int)

    new_tx_df['accX'] = account_name

    df_out = (new_tx_df[['date', 'accX', 'accY', 'net_amt', 'ITEM', '_item',
                         'id', 'mode']] .set_index('date'))

    # from df_out modes organise and amend the dbs:
        # mode -1: already unknown so nfa
        # mode  0: new unknowns, so append -> unknowns_db DONE
        # mode  1: already known, so nfa
        # mode  2: already fuzzy matched, so nfa
        # (mode 3: new fuzzy match - already amended in categorise()*)
        

    # first the new unknowns (mode = 0)
    new_unknowns =  df_out.loc[df_out['mode']==0]
    new_unknowns = new_unknowns[['_item', 'accX','accY']].reset_index(drop=True)
    unknowns_db = unknowns_db.reset_index(drop=False)

    unknowns_out = pd.concat([unknowns_db, new_unknowns], sort=True).drop_duplicates() 
    unknowns_out.to_csv(unknowns_path, index=False)

    # now the new fuzzy matches - already added to db in RAM
    fuzzy_db.to_csv(fuzzy_db_path, date_format="%d/%m/%Y")

    # *problem is that the fields required to fill in the fuzzy_db are not
    # available.  Need eg the best match result that led to the fuzzy find.
    # That stuff is hidden in categorise()
    # Possible solutions:
        # - have categorise return mode values that allow the match to be looked up
        #   (it is from tx_db, so just need the id).  Started trying this below but
        #   it's not easy (maybe impossible) to overwrite the column in df_out with 
        #   a series of looked-up ITEMs from tx_db (got with the series of ids).
        #   So this is commented out below.

        # - do the modification of fuzzy_db in the categorise() loop.  That is, 
        #   as soon as a match is found, append it to tx_db.  If going to do this, 
        #   which does seem best, maybe better to do all the db appends in the 
        #   categorise loop. NOW DOING THIS


    # finally the tx_db
    if os.path.isfile(tx_db_path):
        df_out.to_csv(tx_db_path, mode="a", header=False, date_format="%d/%m/%Y")
    else:
        df_out.to_csv(tx_db_path, mode="w", header=True, date_format="%d/%m/%Y")


    if return_df: return df_out


def update_unknowns(unknowns_path, account, tx_db=None, tx_db_path=None,
                    return_df=False):
    """Take a csv file of unknowns for which some have had accY
    categories manually completed.

    For those that are completed, update the relevant fields in a tx_db. 

    Delete from the unknowns csv
    """

    if tx_db is None:
        if tx_db_path is None:
            print('need a tx_db or a path')
            return 1
        else:
            tx_db = pd.read_csv(tx_db_path, index_col='date')

    unknowns = pd.read_csv(unknowns_path, index_col='_item')

    to_edit = unknowns.loc[unknowns['accY'] != 'unknown']

    base_masklist = [tx_db['accX'] == account,
                     tx_db['accY'] == 'unknown']

    for tx in to_edit.index:
        masks = base_masklist + [tx_db['ITEM'].str.lower().str.strip() == tx]
        new_val = to_edit.loc[tx,'accY'] 
        edit_tx(df=tx_db, target_col='accY', new_val=new_val, masks=masks)

    unknowns.loc[unknowns['accY'] == 'unknown'].to_csv(unknowns_path)

    if tx_db_path is not None:
        tx_db.to_csv(tx_db_path)

    if return_df:
        return tx_db



def edit_tx(df, target_col, new_val, masks, return_df=False):
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

    if return_df: return df


