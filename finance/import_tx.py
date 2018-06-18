import pandas as pd

from finance import *

def import_txs(file, account_name, parser, accounts, categ_map):
    """Import raw transactions and return a tx_df in standard format,
    with date index, and columns: from, to, amt

    TODO:
        - add unique ID field
        - categorise from and to cols for 'from_to' type
        - append to any existing past tx_df (and sort etc)
        - trigger account creation for new categories

    file         : the path of the raw transaction csv file

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns
                   
    parser       : dict with instructions for processing the raw tx file
                    - 'input_type' : 'from_to', 'credit_debit' or 'net_amt'
                    - 'mapping'    : dict of mappings for column labels
                                     (new labels are keys, old are values)

                                     - must contain mappings to all reqd cols

    accounts     : the current list of account instances, from which tx 
                   parsers can be retrieved [MAYBE - NOT CURRENTLY USED]

    categ_map    : csv file containing known mappings from 'item' to 
                   category

    """

    raw_df = pd.read_csv(file, parse_dates=[parser['mappings']['date']])

    # select only the columns reqd
    raw_df = raw_df[list(parser['mappings'].values())]

    # map to the standard labels
    raw_df.columns = parser['mappings'].keys()

    # unless already in 'from_to', do the conversion
    if parser['input_type'] != 'from_to':

        # first, from 'credit_debit' to 'net_amt'
        if parser['input_type'] == 'credit_debit':
            raw_df['net_amt'] = (raw_df['debit_amt']
                                 .subtract(raw_df['credit_amt'], fill_value=0))

        # then to 'from_to', also assigning categories
        raw_df['category'] = categorise(raw_df['item'],
                                        new_categ_map_path='temp_new_cat_path.csv')

        raw_df[['from', 'to']] = consol_debit_credit(raw_df, account_name)
    
    raw_df['amt'] = raw_df['net_amt'].abs()
    df_out = raw_df[['date', 'from', 'to', 'amt', 'item']].set_index('date')

    return df_out



