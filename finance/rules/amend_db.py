# myfin/finance/rules/amend_db.py

"""
GENERAL PATTERN

args:  tx_db, rule

From the rule, make:
    a mask to filter the tx_db (arbitrarily)
    a column to change
    a list of new values of same length as selection
    (or a single value)

Use the mask to split this bit off as a copy.

Apply the new values

Add back to the tx_db and return

fl
"""

import pandas as pd

from finance.rules.Rule import Rule, Selection

def amend_db(df, rule):
    """
    Amend the passed df according to the passed rule and return it.
    """

    mask = make_mask(rule.selections, df)

    to_change = df.loc[mask].copy()
    remainder = df.loc[~mask]

    to_change[rule.cols_to_change] = rule.new_vals

    return pd.concat([remainder, to_change])


def make_mask(selections, df):
    """
    Turn the passed selections into a mask for filtering the passed df
    """

    mask_out = True

    for s in selections:

        if s.operation == 'equals':
            m = df[s.column] == s.term

        elif s.operation == 'not_equals':
            m = df[s.column] != s.term

        elif s.operation == 'contains':
            m = df[s.column].str.contains(s.term)

        elif s.operation == 'not_contains':
            m = ~df[s.column].str.contains(s.term)

        mask_out &= m

    return mask_out


def quick_amend(tx_db, tx_id, accY, broadcast=True, save_rule=False):
    """
    For an input tx_id number, change the accY to passed value.

    By default broadcast to all other txs with the corresponding _item.
    """

    if broadcast:
        tx = tx_db.loc[tx_db['id'] == tx_id]
        _item = tx['_item'].values[0]
        tx_db.loc[tx_db['_item'] == _item, ['accY','mode']] = accY, 'confirmed'

    else:
        tx_db.loc[tx_db['id'] == tx_id, ['accY','mode']] = accY, 'confirmed'

    return tx_db

    # rule = Rule(rule_id='quick_amend_' + str(tx_id),






