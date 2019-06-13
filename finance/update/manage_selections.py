# myfin/finance/update/manage_selections.py
"""
Module contains function to manage the list of selections
used in an update console session.
"""

from finance.update.print_selections import print_selections
from finance.update.Rule import Selection

OP_MAP = {
    'e': 'equals',
    'u': 'not_equals', # unequal
    'c': 'contains',
    'n': 'not_contains'
}

def manage_selections(action, selections, tx_db, lpad=20):
    """
    Function to manage the list of selections used in an
    update console session.
    """

    # first parse the main command and any args
    if len(action.split()) < 1:
        return

    else:
        main_cmd = action.split()[0]
        args = action.split()[1:]


    if main_cmd == 'd' and args is not None:

        try:
            to_del = int(args[0])

            print('deleting selection #', to_del)
            del selections[to_del]

            if len(args) > 1:
                print('OTHERS IGNORED')

            print_selections(selections, tx_db)
            return

        except:
            print('cannot get an index from', args[0])
            return


    if main_cmd == 'a' and args is not None:

        if len(args) != 3:
            print('need exactly 3 args: column, operator, term')
            return

        if not args[0] in tx_db.columns:
            print()
            print(f'{args[0]} is not a column of the tx_db')
            print(list(tx_db.columns))
            print()
            return


        if not args[1] in OP_MAP.keys():
            print('\noperation must be one of:\n'
                  '   e: "equals"'
                  '   u: "unequals"'
                  '   c: "contains"'
                  '   n: "not_contains"\n')
            return

        selection = Selection(column=args[0],
                              operation=OP_MAP[args[1]],
                              term=args[2])

        selections.append(selection)

        print_selections(selections, tx_db)

