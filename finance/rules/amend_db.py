# myfin/finance/amend_db.py

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
