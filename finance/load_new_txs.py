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
    unknowns_df = unknowns_df[['accX','accY']]

    if os.path.isfile(unknowns_path):
        unknowns_df.to_csv(unknowns_path, mode="a", header=False)
    else:
        unknowns_df.to_csv(unknowns_path, mode="w", header=True)

    if return_df: return df_out


def update_category(item, accX, old_accY, new_accY, txdf):
    """Update the assignation of accY category in txdf for rows labelled item:
        - find rows of item associated with accX (or all, if accX is none),
          with old_accY as accY (or all if old_accY is none)
        - overwrite accY with new_accY 

        Remember the input item will be lower()ed and stripp()ed
    """
    # 1. get the txdf selection
    mask =    (txdf['item'].str.lower().str.strip() == item) \
            & (txdf['accX'] == accX)                         \
            & (txdf['accY'] == old_accY)

    select_df = txdf.loc[mask]

