from pathlib import Path
from os import get_terminal_size
import pandas as pd
from hashlib import sha1

from termcolor import cprint

def db_compare(target, test, assertion=False):
    """
    Compares two dataframes.
    First naively applies target.equals(test), returns True
    (and asserts True) if True.

    If not, displays differences in rows, and across whole dfs,
    then returns and asserts False.
    """

    # get rid of pesky nans which compare unequal
    test = test.copy().fillna("BLANK").sort_index()
    target = target.copy().fillna("BLANK").sort_index()

    print(target.shape, "vs", test.shape, end=": ")
    # simple equality test
    if target.equals(test):
        cprint('dbs equal by df.equals()', color='green', attrs=['bold'])
        if assertion:
            assert True
        return True
    else:
        cprint('NOT EQUAL', color='red', attrs=['bold'])

    # if df.equals() fails, compare rows then whole dfs
    # before asserting and returning False

    # Compare ROWS, displaying diff if there is one
    test_rows = set(test.index) 
    target_rows = set(target.index) 
    test_cols = set(test.columns) 
    target_cols = set(target.columns) 

    if test_rows != target_rows:
        print_title('ROW DIFFERENCE')
        print('\nTest rows:')
        for row in test_rows:
            if row in target_rows:
                print("--", end=" ")
            else:
                print("**", end=" ")
            print(row)
        print('\nTarget rows:')
        for row in target_rows:
            if row in test_rows:
                print("--", end=" ")
            else:
                print("++", end=" ")
            print(row)

        assert_False = True

    # Print df comparisons / differences
    print_title('DF COMPARISONS')

    # mask - NB a superset / union with all rows and columns
    mask = test.eq(target)

    # print the result of eq() but using '-' and 'X' markers
    mask_diff = mask.copy()
    mask_diff[mask] = '-'
    mask_diff[~mask] = 'X'
    print('\nComparison over union')
    print(mask_diff)

    # print diffs: in x, print '-' where x == y, otherwise print x

    test_diff = test.copy()
    test_diff = test_diff.where(~mask, other='-')

    target_diff = target.copy()
    target_diff = target_diff.where(~mask, other='-')

    print('\nIn TEST, not in target')
    print(test_diff)

    print('\nIn TARGET, not in test')
    print(target_diff)

    if assertion:
        assert False

    return False

def make_test_dbs(master_path):
    """
    From a master xls, make input and targets for all dbs:
        tx_db, unknowns_db, cat_db, fuzzy_db

    Return a dict of all eight
    """

    masters = {'input': pd.read_excel(master_path, usecols=range(0,5)),
               'target': pd.read_excel(master_path, usecols=range(6,11))}

    # trim off the 'explanation' section
    if 'explanation' in masters['input'].index:
        last_row = masters['input'].index.get_loc('explanation')
        masters['input'] = masters['input'].iloc[:last_row]
        masters['target'] = masters['target'].iloc[:last_row]

    new_index = []
    last = None

    for i in masters['input'].index:
        if not pd.isna(i):
            new_index.append(i)
            last = i
        else:
            new_index.append(last)

    dbs = {'input': {}, 'target': {}}

    for master in masters:
        masters[master].index = new_index
        for db in set(new_index):
            dbs[master][db] = masters[master].loc[db].reset_index(drop=True)
            dbs[master][db] = curate_db(dbs[master][db], db)

    return dbs


def curate_db(df, db):

    # trim off na rows AT THE END ONLY
    # if len(df):
    #     while len(df) and pd.isna(df.iloc[-1]).all():
    #         df = df[:-1].copy()

    df = df.copy()
    df.dropna(how='all', inplace=True)
    if db != 'fuzzy_db':
        df.drop('status', axis=1, inplace=True)

    if db != 'tx_db':
        df.set_index('_item', drop=True, inplace=True)

    if db == 'tx_db':
        df.index = pd.date_range(start='1/1/2000', periods=len(df))
        df.index.name = 'date'
        df['net_amt'] = [get_net_amt_hash(x) for x in range(len(df))]
        df['id'] = list(range(10, 10 + len(df)))
        df['mode'] = 'not set'
        df['source'] = 'make_test_dbs'

    return df


def get_net_amt_hash(index_number):
    """
    For an input int (or string), return a float in format xx.xx

    Intended to provide predictable net_amts for tx_db
    """

    bytes_in = str.encode(str(index_number))
    digest = sha1(bytes_in).digest()

    str_of_int = str(int.from_bytes(digest, 'big'))

    return int(str_of_int[-4:]) / 100


def aggregate_dbs(dbs):
    """
    Concatenates full set of dbs for pasting / saving to xls for inspection
    Input a dict of dbs
    """
    
    cols = ['_item', 'accX', 'accY', 'status']

    df_out = pd.DataFrame(columns=cols)

    for db in dbs:
        df_out.loc[len(df_out)] = [db] + ([""] * (len(df_out.columns) - 1))
        df_out = df_out.append(dbs[db].reset_index(drop=False),
                               sort=False, ignore_index=True)

    return df_out[cols]


def print_title(title_string=""):
    """
    Prints a nice title right across the terminal
    """
    if title_string:
        title_string = " " + title_string + " "

    term_cols = get_terminal_size()[0]

    bar1 = int((term_cols - len(title_string)) / 2)
    bar2 = term_cols - len(title_string) - bar1

    print('\n')
    print("".join(["*" * bar1, title_string, "*" * bar1]))


def print_db_dicts(dbs):
    """
    Helper which prints dbs ('tx_db', 'fuzzy_db' etc) from all members
    of a dict of dbs (eg 'input', 'target', 'test')
    """

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

            if db_name == 'tx_db':
                cols = ['_item', 'accX', 'accY']
            else:
                cols = dbs[stage][db_name].columns

            df = dbs[stage][db_name][cols].sort_index()

            if len(df):
                print(df) 
            else:
                print('--- empty df ---')




def print_dbs(dbs):
    """
    Helper which prints all dbs in a dict with 'input' and 'target' sets, 
    each comprising 'tx_db', 'unknowns_db' etc
    """
    if not 'input' in dbs.keys():
        print_xdbs(dbs)
        return

    for db in dbs['input']: 
        print_title(db)
        print('\nINPUT') 

        if db == 'tx_db':
            cols = ['_item', 'accX', 'accY']
        else:
            cols = dbs['input'][db].columns

        print(dbs['input'][db][cols].sort_index()) 
        print('\nTARGET') 
        print(dbs['target'][db][cols].sort_index())


def print_xdbs(dbs):
    """
    Prints all dbs in a dict of 'tx_db', 'unknowns_db' etc
    """

    for db in dbs: 
        print_title(db)

        if db == 'tx_db':
            cols = ['_item', 'accX', 'accY']
        else:
            cols = dbs[db].columns

        print(dbs[db][cols].sort_index()) 
