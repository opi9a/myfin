# myfin/finance/load_new_txs/clean_tx_df.py

import pandas as pd


def clean_tx_df(df):
    """
    Make sure imported columns are sanitary.
    """

    df['date'] = pd.DatetimeIndex(df['date'])

    for label in ['net_amt', 'debit_amt', 'credit_amt']:
        if label in df.columns:
            df[label] = pd.to_numeric(df[label], errors='coerce')

    return df


