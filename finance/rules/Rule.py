# myfin/finance/rules/Rule.py
"""
The Rule class carries information to execute an amendment of a tx db.

It comprises:

    - an optional rule_id
        - eg 'rule1'

    - an arbitrary number of Selection conditions which can be used to
      make a mask for filtering the tx_db, and selecting the rows to be
      amended.

      eg: [ Selection('column'='accX',
                      'operation'='equals',
                      'term'='acc1'),
                      ),
            Selection('column'='_item',
                      'operation'='contains',
                      'term'='orange'),
                      ),
          ]

    - a list of columns to be changed
        - eg ['accY', 'mode']

    - a list of new values for the columns to be changed
        - eg ['new_accY', 'assigned_by_rule1']

The component Selection class is a namedtuple with the fields:
    - 'column'   # the column of the tx_db to interrogate
    - 'operation'# the logical operation to use, from:
        - 'equals'
        - 'not_equals',
        - 'contains',
        - 'not_contains'
    - 'term'     # the other input to the logical comparison

JSON SERIALIZING

A rule object can be serialized with its __dict__ attribute:

    >>> rule = Rule('r1',
                    [Selection('accX', 'equals', 'acc1')],
                    ['accY', 'mode'],
                    ['newY', 'new_mode'])

    >>> rule_json = json.dumps(rule.__dict__)

    >>> rule_regen = rule_from_json(rule_json)

    >>> rule_json == rule
    True
"""

from collections import namedtuple
import json


Selection = namedtuple('selection', 'column operation term')


class Rule:
    """
    class Rule:
        name, optional
        selections # a list of conditions, together making a mask for tx_db
        cols_to_change
        new_vals

    """

    def __init__(self, rule_id=None, selections=None,
                 cols_to_change=None, new_vals=None):
        """
        A list of selector_cols, with selection parameters, identifies
        the rows to change.
        """

        self.rule_id = rule_id

        if selections is None:
            self.selections = []
        elif not isinstance(selections, list):
            print('is not a list')
            self.selections = [selections]
        else:
            self.selections = selections

        self.cols_to_change = cols_to_change
        self.new_vals = new_vals


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

            if i == len(self.selections) - 1:
                line_str.append("],")
            else:
                line_str.append(",")

            sel_strs.append("".join(line_str))

        repr_args.append("\n".join(sel_strs))

        if self.cols_to_change is not None:
            cols_to_change = f'{self.cols_to_change},'
        else:
            cols_to_change = f'None,'
        repr_args.append(''.ljust(pad1) + 'cols_to_change=' + cols_to_change)

        if self.new_vals is not None:
            new_vals = f'{self.new_vals})'
        else:
            new_vals = f'None)'

        repr_args.append(''.ljust(pad1) + 'new_vals=' + new_vals)

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
        str_args.append('cols_to_change:'.ljust(pad) + str(self.cols_to_change))
        str_args.append('new_vals:'.ljust(pad) + str(self.new_vals))

        return "\n".join(str_args)


    def __eq__(self, other):
        """
        Just compare all attributes
        """

        return all([self.rule_id == other.rule_id,
                    self.selections == other.selections,
                    self.cols_to_change == other.cols_to_change,
                    self.new_vals == other.new_vals])


        


def rule_from_json(rule_json):
    """
    Returns a Rule object from a passed json string.
    """

    rule_dict = json.loads(rule_json)

    return Rule(rule_id=rule_dict['rule_id'],
                selections=[Selection(*x) for x in rule_dict['selections']],
                cols_to_change=rule_dict['cols_to_change'],
                new_vals=rule_dict['new_vals'],
               )


TEST_RULE = Rule(rule_id='test_rule',
                 selections=[Selection('accX', 'equals', 'acc1'),
                             Selection('_item', 'contains', 'orange')],
                 cols_to_change=['accY', 'mode'],
                 new_vals=['new_Y', 'new_mode'])

