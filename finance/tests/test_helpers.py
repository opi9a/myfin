# myfin/finance/tests/test_helpers.py

from pathlib import Path
from os import get_terminal_size
import pandas as pd
from hashlib import sha1

from termcolor import cprint


def make_parser(input_type = 'credit_debit',
                  date_format = '%d/%m/%Y',
                  debit_sign = 'positive',
                  date = 'date',
                  ITEM = 'ITEM',
                  net_amt = 'net_amt',
                  credit_amt = 'credit_amt',
                  debit_amt = 'debit_amt',
                  balance = None,
                  y_amt = None,
               ):
    """
    Generate a parser dict for controlling import of new txs from csv.

    input_type      : 'debit_credit' or 'net_amt'
    date_format     : strftime structure, eg see default
    debit_sign      : if net_amt, are debits shown as 'positive' or 'negative'

    the rest are column name mappings - that is, the names in the input csv
    for the columns corresponding to 'date' 'ITEM', 'net_amt' etc

    Will automatically remove mappings that are not reqd, eg will remove 'net_amt'
    if the input type is 'debit_credit'.
    """

    parser = dict(input_type = input_type,
                  date_format = date_format,
                  debit_sign = debit_sign,
                  map = dict(date = date,
                             ITEM = ITEM,
                             net_amt = net_amt,
                             credit_amt = credit_amt,
                             debit_amt = debit_amt,
                            )
                 )

    if input_type == 'credit_debit':
        del parser['map']['net_amt']

    elif input_type == 'net_amt':
        del parser['map']['credit_amt']
        del parser['map']['debit_amt']

    else:
        print('need an input type of either "net_amt" or "credit_debit"')

    if balance is not None:
        parser['map']['balance'] = balance

    if y_amt is not None:
        parser['map']['y_amt'] = y_amt

    return parser


def print_title(title_string="", char="*", attrs=None, color=None, borders=False):
    """
    Prints a nice title right across the terminal
    """
    if attrs is None:
        attrs = []

    if title_string:
        title_string = " " + title_string + " "

    term_cols = get_terminal_size()[0]

    bar1 = int((term_cols - len(title_string)) / 2)
    bar2 = term_cols - len(title_string) - bar1

    print('')
    if borders:
        cprint(char * term_cols, attrs=attrs, color=color)

    cprint("".join([char * bar1, title_string, char * bar1]), color=color, attrs=attrs)

    if borders:
        cprint(char * term_cols, attrs=attrs, color=color)
    print('')



def print_db_dicts(dbs, ignore_cols=['source', 'id']):
    """
    Helper which prints dbs ('tx_db', 'fuzzy_db' etc) from all members
    of a dict of dbs (eg 'input', 'target', 'test')
    """

    # check not a single level
    try:
        upper_level_dicts = [isinstance(dbs[x], dict) for x in dbs]
    except:
        print('cannot recognise dbs passed')
        return

    print(upper_level_dicts)
    if not all(upper_level_dicts):
        print_db_dfs(dbs, ignore_cols)
        return
    
    # first get the names of dbs, at the bottom level
    db_names = []

    for stage in dbs:
        db_names.extend(dbs[stage].keys())

    db_names = set(db_names)

    # use these to structure the output
    for db_name in db_names:
        print_title(db_name)
        for stage in dbs:
            print()
            cprint(" - " + stage.upper(), attrs=['bold'])

            df = dbs[stage][db_name]
            cols = df.columns.difference(ignore_cols)
            df = df[cols].sort_index()

            if len(df):
                print(df) 
            else:
                print('--- empty df ---')


def print_db_dfs(dbs, ignore_cols=None):
    """
    Prints all dfs in a dict of 'tx_db', 'unknowns_db' etc
    """

    if ignore_cols is None:
        ignore_cols = ['source', 'id']

    for db in dbs:
        print('with db', db, 'type:', type(dbs[db]))

    # for some reason isinstance(df, pd.DataFrame) doesn't work, so hack:
    if not all(['DataFrame' in str(type(dbs[x])) for x in dbs]):
        print('need a dict of dfs')
        return

    for db in dbs: 
        print_title(db)

        if db == 'tx_db':
            cols = ['_item', 'accX', 'accY']
        else:
            cols = dbs[db].columns

        df = dbs[db][cols].sort_index()

        if len(df):
            print(df) 
        else:
            print('--- empty df ---')

