# myfin/finance/rules/update_session.py

"""
Console session for updating tx_db by building up lists of selections, 
and applying as masks - to view slices of the df, and to set new values.

Save as (list of) rules in json.

Commands: DOING DIFFERENT NOW USING CMD WITH AUTOCOMPLETE,
          KEPT HERE FOR GUIDE

    s   show selections
        - a list of whatever's been added, initially empty

    sa  add a selection.  Arguments:
        <col> <op> <term>:

            col: literal name of the column (case insensitive? just initials?)

            op:
                e   : equals
                u   : not_equals
                c   : contains
                n   : not_contains (absent)

            term:   literal term for comparision / search

    ds  show df filtered by selections

    cc  cols_to_change, initially empty

    nv  new_vals, initially empty

    q   quit


Pass tx_db to function, return modified
"""

import cmd

from termcolor import cprint

from finance.rules.Rule import Rule, Selection 
from finance.rules.amend_db import make_mask

OP_MAP = {
    'e': 'equals',
    'u': 'not_equals', # unequal
    'c': 'contains',
    'n': 'not_contains'
}

BASE_TX_DB_COLS = ['accX', 'accY', '_item', 'net_amt'] # NB 'date' is index


def console_session(tx_db):
    """
    Run a console session for filtering and amending tx_db.

    TODO:
        show stats for selection (or whole db), eg number of unknowns
    """

    # save an unadulterated copy
    init_tx_db = tx_db.copy()

    selections = []

    # have to define this class in the calling function to access vars
    # (i.e. tx_db, selections)
    class Session(cmd.Cmd):
        """
        Class for the session, from cmd.
        """
        prompt = ('--> ')

        def do_echo(self, arg):
            'test function to print args'
            print('arg is:', arg)

        def do_append(self, arg):
            'append to the list of selections'
            selections.append(parse_add_selection(arg))
            print_selections(selections, tx_db)

        def do_show_tx_db(self, arg):
            'display the tx_db with current selections applied'
            mask = make_mask(selections, tx_db)
            print_tx_db(tx_db, mask, arg)

        def do_quit(self, arg):
            'exit the console session'
            return True

    Session().cmdloop()


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


def print_selections(selections, tx_db):
    """
    Prettily prints the list of selections
    """

    def _pr_line(line, pads, color=None, attrs=None):
        """
        Pass a list of elements to print, with pads
        """

        for i, elem in enumerate(line):
            cprint(elem.ljust(pads[i]), end="",
                   attrs=attrs, color=color)

        print()


    pads = [20]*3

    print('\nSelections now:')
    _pr_line(['column', 'operation', 'term'], pads,
             attrs=['bold'])

    for selection in selections:
        _pr_line(selection, pads)

    mask = make_mask(selections, tx_db)

    print()

    print(f'< Selects {len(tx_db.loc[mask])} of {len(tx_db)} transactions >',
           end="\n")

    print()


def parse_add_selection(arg_str):
    """
    Parses a string containing a command for creating a selection.

    Structure:  <column> <operation> <term>
    """

    cmds = arg_str.split()

    selection = Selection(column=cmds[0],
                          operation=OP_MAP[cmds[1]],
                          term=cmds[2])

    return selection





    
