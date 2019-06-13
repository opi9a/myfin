# myfin/finance/tests/test_amend_db.py
"""
Functions to test the amend_db() function, which applies a rule to
amend a dataframe of transactions.
"""

from finance.update.amend_db import amend_db
from finance.update.Rule import Selection, Rule

from finance.tests.db_compare import db_compare
from finance.tests.test_helpers import print_title
from finance.tests.make_test_constructs import make_raw_dfs_from_master_xls

MASTER_XLSX_PATH = ('~/shared/projects/myfin/testing/xlsx_masters/'
                    'apply_rules_master.xlsx')


OP_MAP = {
    '=': 'equals',
    '!=': 'not_equals',
    'cont': 'contains',
    'ncont': 'not_contains'
}


def test_amend_db(master_xls_path=MASTER_XLSX_PATH):
    """
    Makes a set of rules, an input df to amend and a target df
    from a master xls.

    Applies the rules to the input df to get a test output using amend_db,
    and compares to target output.
    """

    print_title('amend_db()', borders=False, attrs=['bold'],
                                      color='magenta', char='-')

    # make the rules
    rules = get_rules(master_xls_path)

    # get the test_output by repeated application of amend_db with each rule
    raw_dfs = make_raw_dfs_from_master_xls(master_xls_path)
    test_output = raw_dfs['input']['input_db'].copy()

    for rule in rules:
        test_output = amend_db(test_output, rule)

    target = raw_dfs['target']['input_db']

    db_compare(test_output, target)


def get_rules(master_xls_path):
    """
    For an input of raw dfs (read from a master xlsx), return the
    rules (if present correctly)
    """

    raw_dfs = make_raw_dfs_from_master_xls(master_xls_path)
    raw_rules = raw_dfs['input']['rules']

    rules = []

    for row in raw_rules.index:

        sel1_tokens = raw_rules.loc[row, 'selection1'].split()

        sel1 = Selection(column=sel1_tokens[0],
                         operation=OP_MAP[sel1_tokens[1]],
                         term=sel1_tokens[2])

        sel2_tokens = raw_rules.loc[row, 'selection2'].split()

        sel2 = Selection(column=sel2_tokens[0],
                         operation=OP_MAP[sel2_tokens[1]],
                         term=sel2_tokens[2])

        cols_to_change = raw_rules.loc[row, 'cols_to_change'].split()
        new_vals = raw_rules.loc[row, 'new_vals'].split()

        rules.append(Rule(rule_id=raw_rules.loc[row, 'rule_id'],
                          selections=[sel1, sel2],
                          cols_to_change=cols_to_change,
                          new_vals=new_vals,
                         )
                    )
    return rules

