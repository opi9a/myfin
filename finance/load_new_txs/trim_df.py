# myfin/finance/load_new_txs/trim_df.py

from pathlib import Path
import pandas as pd
from termcolor import cprint

def trim_df(df, tx_db, confirm_dups=False):
    """
    For an input df of new txs and an existing tx_db, return the input
    df trimmed of txs found in tx_db.
    """

    # use common cols to index both dfs
    common_cols = set(tx_db.reset_index().columns).intersection(df.columns)
    common_cols = [x for x in common_cols if x != 'source']

    # best to put everything in the index and use built-in set logic
    tx_db_by_cc = tx_db.reset_index().set_index(common_cols)
    df_by_cc = df.reset_index(drop=True).set_index(common_cols)

    duplicate_tups = df_by_cc.index.intersection(tx_db_by_cc.index)
    unique_tups = df_by_cc.index.difference(tx_db_by_cc.index)

    duplicates = df_by_cc.loc[duplicate_tups].reset_index().set_index('date')
    uniques = df_by_cc.loc[unique_tups].reset_index().set_index('date')

    if uniques.empty:
        print('ALL TXS TRIMMED OFF!!!')
        print('This may mean the txs are being reloaded, and are already'
              ' in the tx_db')

    if confirm_dups and not duplicates.empty:
        print(f'Found {len(duplicates)} duplicates')
        cprint(f'Confirm manually - otherwise will drop all (y/N)?',
               attrs=['bold'], end="")
        confirm = input("    ")

        if not confirm or confirm.lower()[0] != 'y':
            return uniques

        for i, row in enumerate(duplicates.to_string().split('\n')):
            if i < 2:
                print(row)
                continue
            print()
            print(row)
            cprint('Drop this (Y/n)?    ', attrs=['bold'], end="")
            drop = input()

            if drop and drop.lower()[0] == 'n':
                # remember 2 title rows in df.to_string
                uniques = uniques.append(duplicates.iloc[i - 2])


    return uniques


