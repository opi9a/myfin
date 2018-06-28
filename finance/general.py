import pandas as pd
import numpy as np
import os

# load the tx dataset


def load_tx(path=None):
    """Load the transactions data

    Replace this with a function to load everything:
        - past tx_df
        - notes json
        - list of accounts
        - future tx_df
        - (any rules about future that have to exist separately)
    """

    if path is None:
        path = "tx.pkl"

    return pd.read_pickle(path)


def genfunc():
    print('called func defined in general.py')


def curate_categories():
    """
        Alert user and ask for assignment
        Eg in a csv file that can be changed and scanned
        Update categories dict / mapping with any changes
    """


def load_categ_map(path='categ_map.pkl'):
    return pd.read_pickle(path)

def consol_debit_credit(df_in, acc_name):
    """take a df with debit and credit cols, plus category col
    return a pair of columns with from and to, plus a column which says 
    in which direction the item assignation referred to (i.e. was it
    'from', eg spending from an account, or 'to', eg income)
    """

    if 'category' in df_in.columns:
        df_out = pd.DataFrame(df_in['category'])
    else:
        df_out = pd.DataFrame(np.array(['$OUT'] * len(df_in)))


    df_out['x'] = acc_name
    df_out['y'] = 'to'
    df_out.columns = ['to', 'from', 'item_from_to']

    for row in df_in.iterrows():
        if row[1].loc['net_amt'] < 0:
            df_out.iloc[row[0],0] = acc_name
            df_out.iloc[row[0],1] = row[1].loc['category']
            df_out.iloc[row[0],2] = 'from'

    return df_out[['from', 'to', 'item_from_to']]


def make_parser(input_type='credit_debit', date_format='%d/%m/%Y',
                date='xdate', item='xitem', debit_amt='xdebit_amt', credit_amt='xcredit_amt'):
    """Helper to generate a parser dictionary.
    """
    return dict(input_type=input_type,
                date_format=date_format,
                mappings=dict(date=date,
                              item=item,
                              debit_amt=debit_amt,
                              credit_amt=credit_amt))








