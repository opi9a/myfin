import pandas as pd
import numpy as np
import os

from finance.categorise import categorise, itemise
from finance.general import consol_debit_credit

def load_new_txs(new_tx_paths, txdb_path=None, unknowns_path=None,
                 account_name=None, parser=None,
                 return_df=False):

    """Import raw transactions and return a tx_df in standard format,
    with date index, and columns: from, to, amt

    new_tx_paths : a list of csv files with new transactions
    
    txdb_path:     the path of the existing tx database. 
                   (or a new one to create)

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns

    parser       : dict with instructions for processing the raw tx raw_tx_path
                    - 'input_type' : 'from_to', 'credit_debit' or 'net_amt'
                    - 'date_format': eg "%d/%m/%Y"
                    - 'mapping'    : dict of mappings for column labels
                                     (new labels are keys, old are values)

                                     - must contain mappings to all reqd cols:
                                       ['date', 'from', 'to', 'amt', 'item']


    """

    # 1. aggregate input csvs to a single df
    date_parser = lambda x: pd.datetime.strptime(x, parser['date_format'])
    raw_df = pd.concat([pd.read_csv(f, parse_dates=[parser['mappings']['date']],
                                       skipinitialspace=True,
                                       date_parser=date_parser, dayfirst=True)
                                    for f in new_tx_paths])

    # 2. organise columns using parser
    raw_df = raw_df[list(parser['mappings'].values())]
    raw_df.columns = parser['mappings'].keys()

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        raw_df['net_amt'] = (raw_df['debit_amt']
                             .subtract(raw_df['credit_amt'], fill_value=0))
        
    # 3. read in txdb from csv
    # TODO - handle case if file absent
    txdb = pd.read_csv(txdb_path, index_col='date')

    # 4. call categorise() to get accY and mode columns,
    categ_out = categorise(raw_df['item'], account=account_name, txdb=txdb)
    raw_df['accY'] = [x[0] for x in categ_out]
    raw_df['mode'] = [x[1] for x in categ_out]

    # 5. add id and account name columns to make output df
    max_current = int(pd.read_csv(txdb_path)['id'].max())
    raw_df['id'] = np.arange(max_current + 1,
                             max_current + 1 + len(raw_df)).astype(int)

    raw_df['accX'] = account_name

    df_out = (raw_df[['date', 'item', 'accX', 'accY', 'net_amt', 'mode',
                      'id']] .set_index('date'))
    
    # 6. append to csv on disk - handle if txdb file not already existing
    if os.path.isfile(txdb_path):
        df_out.to_csv(txdb_path, mode="a", header=False, date_format="%d/%m/%Y")
    else:
        df_out.to_csv(txdb_path, mode="w", header=True, date_format="%d/%m/%Y")


    # 7. write out unknowns to unknowns.csv
    unknowns_df = df_out.loc[df_out['accY'] == 'unknown']
    unknowns_df = itemise(unknowns_df, drop_unknowns=False)
    unknowns_df = unknowns_df[['accX','accY']].reset_index()

    if os.path.isfile(unknowns_path):
        existing_unknowns = pd.read_csv(unknowns_path)
    else:
        existing_unknowns = None

    unknowns_out = pd.concat([existing_unknowns, unknowns_df]).drop_duplicates() 
    unknowns_out.to_csv(unknowns_path, index=False)

    if return_df: return df_out


def update_unknowns(unknowns_path, account, txdb=None, txdb_path=None):
    """Take a csv file of unknowns for which some have had accY
    categories manually completed.

    For those that are completed, update the relevant fields in a txdb. 

    Delete from the unknowns csv
    """

    if txdb is None:
        if txdb_path is None:
            print('need a txdb or a path')
            return 1
        else:
            txdb = pd.read_csv(txdb_path, index_col='date')

    unknowns = pd.read_csv(unknowns_path, index_col='item')

    to_edit = unknowns.loc[unknowns['accY'] != 'unknown']

    base_masklist = [txdb['accX'] == account,
                     txdb['accY'] == 'unknown']

    for tx in to_edit.index:
        masks = base_masklist + [txdb['item'].str.lower().str.strip() == tx]
        new_val = to_edit.loc[tx,'accY'] 
        edit_tx(df=txdb, target_col='accY', new_val=new_val, masks=masks)

    unknowns.loc[unknowns['accY'] == 'unknown'].to_csv(unknowns_path)

    if txdb_path is not None:
        txdb.to_csv(txdb_path)
    return txdb



def edit_tx(df, target_col, new_val, masks, return_df=False):
    """Edits transactions of an input df by selection based on columns

    target_col  : the column to be edited

    new_val     : the value to be inserted at selected fields

    masks       : a list of boolean df masks to apply to select rows

                - eg [df['item'].str.lower().strip() == 'newt cuffs',
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


