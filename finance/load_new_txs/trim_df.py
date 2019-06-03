# myfin/finance/load_new_txs/trim_df.py

from pathlib import Path
import pandas as pd

def trim_df(df, tx_db):
    """
    For an input df of new txs and an existing tx_db, return the input
    df trimmed of txs found in tx_db.
    """

    tx_db = tx_db.reset_index().sort_values(['date', '_item'])
    df = df.sort_values(['date', '_item'])

    # make sure only comparing the same columns
    common_cols = [x for x in set(tx_db.columns).intersection(df.columns)
                     if x != 'source']

    # get tx_db and new as indexes and use built-in index difference() method
    prev_ind = tx_db.set_index(common_cols).index
    new_ind = df.set_index(common_cols).index

    # subset input df with uniques index
    subset = df.set_index(common_cols).loc[new_ind.difference(prev_ind)]

    return subset.reset_index().set_index('date')

