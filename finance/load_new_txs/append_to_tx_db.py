# myfin/finance/load_new_txs/append_to_tx_db.py

import pandas as pd


def append_to_tx_db(df, tx_db):
    """
    Assign ids to the new txs and append to tx_db
    """
    if len(tx_db):
        max_current = tx_db['id'].max()
    else:
        max_current = 100

    df['id'] = pd.np.arange(max_current + 1,
                         max_current + 1 + len(df)).astype(int)

    missing_cols = tx_db.columns.difference(df.columns)
    cols_to_append = df.columns.intersection(tx_db.columns)

    df_out = tx_db.append(df[cols_to_append], sort=False)
    df_out.index.name = 'date'

    return df_out
