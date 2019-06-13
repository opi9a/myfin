# myfin/finance/update/update_session.py

"""
Console session for updating tx_db by building up lists of selections, 
and applying as masks - to view slices of the df, and to set new values.
"""

import sys
from pathlib import Path

import cmd
import pandas as pd

from finance.update.amend_db import make_mask
from finance.update.print_tx_db import print_tx_db
from finance.update.manage_selections import manage_selections
from finance.update.apply_changes import apply_changes



class Session(cmd.Cmd):
    """
    Class for the session, from cmd.

    Manage selections (add, drop)
    View tx_db under selection
    Set cols to change and new vals
    Apply to tx_db
    Save
    """
    prompt = ('--> ')

    def __init__(self, proj_path=None):
        super().__init__()
        if proj_path is not None:
            self.proj_path = Path(proj_path).absolute()
        else:
            self.proj_path = Path().absolute()
        self.tx_db = pd.read_csv(self.proj_path / 'tx_db.csv')
        self.selections = []
        self.cols_to_change = ['accY', 'mode']
        self.new_vals = None
        # self.rule = None

        self.LPAD = 22

    def do_selections(self, arg):
        'show and manage selections'

        manage_selections(arg, self.selections, self.tx_db, self.LPAD)

    def do_new_vals(self, arg):
        'show and manage the new values to apply to selected rows'
        if arg:
            self.new_vals = arg.split()

        print(self.new_vals)

    def do_cols_to_change(self, arg):
        'show and manage the new values to apply to selected rows'
        if arg:
            self.cols_to_change = arg.split()

        print(self.cols_to_change)

    def do_show_tx_db(self, arg):
        'display the tx_db with current selections applied'
        mask = make_mask(self.selections, self.tx_db)
        print_tx_db(self.tx_db, mask, arg)

    def do_apply(self, arg):
        """
        Amend the tx_db using the current selections, cols_to_change
        and new_vals
        """

        mask = make_mask(self.selections, self.tx_db)

        new_tx_db = apply_changes(self.tx_db, mask,
                                  self.cols_to_change, self.new_vals)

        update_db = input('update the db y/N?'.ljust(self.LPAD))

        if update_db[0].lower() == 'y':
            self.tx_db = new_tx_db
            print(f'changed {sum(mask)} txs')
        else:
            print('OK, leaving it')


    def do_q(self, arg):
        'exit the console session'
        return True


def console_session(proj_path):
    """
    Run a console session for filtering and amending tx_db.
    """

    Session(proj_path).cmdloop()


if __name__ == '__main__':

    if len(sys.argv) == 2:
        proj_path = Path(sys.argv[1]).absolute()
    else:
        proj_path = Path().absolute()

    print('proj_path', proj_path)
    print()

    Session(proj_path).cmdloop()
