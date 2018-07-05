import pandas as pd
import numpy as np
import os

from finance.categorise import categorise
from finance.general import consol_debit_credit

def load_new_txs(raw_tx_path, txdb_file=None,
                 account_name=None, parser=None,
                 return_df=False):
    """Import raw transactions and return a tx_df in standard format,
    with date index, and columns: from, to, amt

    TODO:
        - add unique ID field
        - categorise from and to cols for 'from_to' type

    raw_tx_path  : the path of the raw transaction csv files, or list of files
    
    tx_db_file   : the path of the existing tx database. 
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

    # first, if a list of files has been passed, then simply run the function on each
    if isinstance(raw_tx_path, list):
        for f in raw_tx_path:
            print('loading file', f)
            load_new_txs(f, txdb_file, account_name, parser, return_df)
            return

    if account_name is None: account_name = 'No acc given'

    if txdb_file is None: txdb_file = 'new_txdb.csv'

    if parser is None: 
        print('Need a parser')
        return

    date_parser = lambda x: pd.datetime.strptime(x, parser['date_format'])

    raw_df = pd.read_csv(raw_tx_path, parse_dates=[parser['mappings']['date']],
                         skipinitialspace=True,
                         date_parser=date_parser, dayfirst=True)

    # select only the columns reqd and map to standard labels
    # NB this will be right, tho different, for debit_cred or net_amt
    # - as the parser['mappings'] specifies exactly what's to be used
    raw_df = raw_df[list(parser['mappings'].values())]
    raw_df.columns = parser['mappings'].keys()

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        raw_df['net_amt'] = (raw_df['debit_amt']
                             .subtract(raw_df['credit_amt'], fill_value=0))




    return raw_df

    # unless already in 'from_to', do the conversion
    if parser['input_type'] != 'from_to':

        # first, from 'credit_debit' to 'net_amt'
        if parser['input_type'] == 'credit_debit':
            raw_df['net_amt'] = (raw_df['debit_amt']
                                 .subtract(raw_df['credit_amt'], fill_value=0))

        # then to 'from_to', first assigning categories
        raw_df['category'] = categorise(raw_df['item'], categ_map)

        raw_df[['from', 'to', 'item_from_to']] = \
            consol_debit_credit(raw_df, account_name)

    # clean up, get rid of negative amounts and select/order desired columns
    raw_df['amt'] = raw_df['net_amt'].abs()

    df_out = raw_df[['date', 'from', 'to', 'amt', 'item', 'item_from_to']].set_index('date')


    # get max of current
    max_current = 0
    try:
        max_current = int(pd.read_csv(txdb_file)['uid'].max())
    except: pass

    df_out['uid'] = np.arange(max_current + 1,
                              max_current + 1 + len(df_out)).astype(int)
    
    # handle if txdb file not already existing
    if os.path.isfile(txdb_file):
        df_out.to_csv(txdb_file, mode="a", header=False, date_format="%d/%m/%Y")
    else:
        df_out.to_csv(txdb_file, mode="w", header=True, date_format="%d/%m/%Y")

    if return_df: return df_out



