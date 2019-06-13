# myfin/finance/update/print_selections.py

import pandas as pd
from termcolor import cprint

from finance.update.amend_db import make_mask

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

    pads = [4] + [20]*3

    print('\nSelections now:')

    _pr_line(['#', 'column', 'operation', 'term'], pads,
             attrs=['bold'])

    for i, selection in enumerate(selections):
        _pr_line([str(i)] + list(selection), pads)

    if tx_db is None:
        return

    mask = make_mask(selections, tx_db)

    print()

    print(f'< Selects {len(tx_db.loc[mask])} of {len(tx_db)} transactions >',
           end="\n")

    print()

