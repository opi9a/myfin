# myfin/finance/rules/Rule.py

from collections import namedtuple

Selection = namedtuple('selection', 'column operation term')

class Rule:
    """
    class Rule:
        name, optional
        selections # a list of conditions, together making a mask for tx_db
        col_to_change
        new_val

    """

    def __init__(self, rule_id=None, selections=None,
                 col_to_change=None, new_val=None):
        """
        A list of selector_cols, with selection parameters, identifies
        the rows to change.
        """

        self.rule_id = rule_id

        print('type', type(selections))
        if selections is None:
            self.selections = []
        elif not isinstance(selections, list):
            print('is not a list')
            self.selections = [selections]
        else:
            self.selections = selections

        self.col_to_change = col_to_change
        self.new_val = new_val


    def __repr__(self):

        line1_just = 'Rule('
        line2_just = 'selections=['
        pad1 = len(line1_just)
        pad2 = pad1 + len(line2_just)

        repr_args = []

        if self.rule_id is not None:
            rule_id = f'"{self.rule_id}",'
        else:
            rule_id = f'None,'
        repr_args.append(line1_just + 'rule_id=' + rule_id)

        sel_strs = []

        for i, s in enumerate(self.selections):
            line_str = []
            if i == 0:
                line_str.append(''.ljust(pad1) + line2_just)
            else:
                line_str.append(''.ljust(pad2))

            line_str.append("Selection(")
            line_str.append(f'"{s.column}", "{s.operation}", "{s.term}")')

            if i == len(line_str) - 1:
                line_str.append("],")
            else:
                line_str.append(",")

            sel_strs.append("".join(line_str))

        repr_args.append("\n".join(sel_strs))

        if self.col_to_change is not None:
            col_to_change = f'"{self.col_to_change}",'
        else:
            col_to_change = f'None,'
        repr_args.append(''.ljust(pad1) + 'col_to_change=' + col_to_change)

        if self.new_val is not None:
            new_val = f'"{self.new_val}")'
        else:
            new_val = f'None)'

        repr_args.append(''.ljust(pad1) + 'new_val=' + new_val)

        return "\n".join(repr_args)


    def __str__(self):
        pad = 20
        str_args = []

        str_args.append('rule_id:'.ljust(pad) + str(self.rule_id))

        sel_strs = []

        for i, s in enumerate(self.selections):
            line_str = []
            if i == 0:
                line_str.append('selections:'.ljust(pad - 1))
            else:
                line_str.append(''.ljust(pad - 1))

            line_str.extend([s.column, s.operation, s.term])

            sel_strs.append(" ".join(line_str))

        str_args.append("\n".join(sel_strs))
        str_args.append('col_to_change:'.ljust(pad) + str(self.col_to_change))
        str_args.append('new_val:'.ljust(pad) + str(self.new_val))

        return "\n".join(str_args)


    def add_selection(self, column, operation, term):
        """
        namedtuple Selection:
            column, eg '_item'
            operation, from ['equals', 'not_equals', 'contains', 'not_contains']
            term, eg 'LNK'  # leave case-sensitive, allow searching of 'ITEM'
        """

        if operation not in ['equals', 'not_equals',
                             'contains', 'not_contains']:

            raise ValueError(f'selection operation {operation} not recognized')

        selection = Selection(column=column, operation=operation, term=term)

        self.selections.append(selection)
