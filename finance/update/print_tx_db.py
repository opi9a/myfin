# myfin/finance/update/print_tx_db.py
"""
Module contains function to prettily print a selection of
the tx_db.
"""

from termcolor import cprint

BASE_TX_DB_COLS = ['accX', 'accY', '_item', 'net_amt'] # NB 'date' is index

def print_tx_db(tx_db, mask, other_col_strings, max_rows=20):
    """
    Prettily prints the tx_db, with applied mask.

    List of other_col_strings are added to BASE_TX_DB_COLS
    for printing
    """

    if other_col_strings:
        cols_to_show = BASE_TX_DB_COLS + other_col_strings.split()
    else:
        cols_to_show = BASE_TX_DB_COLS

    tx_to_show = tx_db.loc[mask, cols_to_show]

    print()
    cprint(f'{len(tx_to_show)} of {len(tx_db)} transactions selected, '
           f'showing first {max_rows}',
           attrs=['bold'], end="\n")

    print(tx_to_show.iloc[:max_rows])

    print()
