# myfin/finance/update/apply_changes.py

import pandas as pd


def apply_changes(tx_db, mask, cols_to_change, new_vals):
    """
    Implement the changes specified in passed selections, cols_to_change
    and new_vals in the passed tx_db
    """

    to_change = tx_db.loc[mask].copy()
    remainder = tx_db.loc[~mask]

    to_change[cols_to_change] = new_vals

    return pd.concat([remainder, to_change])

