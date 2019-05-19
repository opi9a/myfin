from pathlib import Path
from os import get_terminal_size
import pandas as pd
from hashlib import sha1

from termcolor import cprint

from finance.init_scripts import make_parser


def db_compare(test, target, db_name=None,
               ignore_cols=['id', 'source', 'mode'],
               assertion=False):
    """
    Compares two dataframes.

    First naively applies target.equals(test), returns True
    (and asserts True) if True.

    If not, displays differences in rows, and across whole dfs,
    then returns and asserts False.

    ignore_cols affects only equality test - the cols will still be printed
    and compared if dfs not equal
    """

    # get rid of pesky nans which compare unequal
    test = test.copy().fillna("BLANK")
    target = target.copy().fillna("BLANK")

    # extend index to include all 'input' cols (i.e. not calculated)
    # - this is to avoid duplicate index entries which complicate comparisons
    test = make_extended_index(test)
    target = make_extended_index(target)

    # make sure columns in same order
    if set(test.columns) != set(target.columns):
        print('test and target have different columns')
        return

    target = target[test.columns]

    if db_name is not None:
        print_title(db_name.upper())

    if ignore_cols:
        print('ignoring columns', ignore_cols, end=" ")
    else:
        print('ignoring no columns', end=" ")

    print(target.shape, "vs", test.shape, end=": ")

    # simple equality test
    cols_to_try = test.columns.difference(ignore_cols)
    if target[cols_to_try].equals(test[cols_to_try]):
        cprint('dbs equal by df.equals()', color='green', attrs=['bold'])
        if assertion:
            assert True
        return True
    else:
        cprint('NOT EQUAL', color='red', attrs=['bold'])

        print('\ntest df:')
        print(test)
        print('\ntarget df:')
        print(target)

    # compare rows
    if set(test.index) != set(target.index):
        print_title(db_name + ':  ROW DIFFERENCES')

        print('Rows in TEST but not in target')
        show_row_diffs(test, target)

        print('Rows in TARGET but not in test')
        show_row_diffs(target, test)

    # Print df comparisons / differences
    print_title(db_name + ':  DF COMPARISONS')

    # mask - NB a superset / union with all rows and columns
    mask = test.eq(target)

    # print the result of eq() but using '-' and 'X' markers
    mask_diff = mask.copy()
    mask_diff = mask_diff.where(mask, other='X')
    mask_diff = mask_diff.where(~mask, other='-')
    print('\nComparison over union')
    print(mask_diff)

    #call diffs func
    print_title(db_name + ':  TEST')
    print()
    show_df_diffs(test, target)
    print_title(db_name + ':  TARGET')
    print()
    show_df_diffs(target, test)

    if assertion:
        assert False

    return False


def make_extended_index(df):

    indexes_to_add = list(df.columns.intersection(['_item', 'accX', 'date']))

    df = df.set_index(indexes_to_add, append=True).sort_index()

    index_list = list(df.index)

    if len(set(index_list)) < len(index_list):
        print('Duplicate extended index entries')

    return df


def show_df_diffs(x, y, verbose=False):
    """
    sort dfs.  For each:
        get orig index
        add any from _item, accX, date
        sort by this index
        ser original index

    get common set of rows
    for each unique row in x:
        see how many rows in y
        try to match them
    """

    pad = 20
    
    df_out = x.copy()

    for i, row in enumerate(x.index):
        if verbose: print_title()
        if verbose: print(f'\nin row {i}:'.ljust(pad), row)

        if not row in y.index:
            if verbose: print('row not found in y\n')
            continue

        for j, col in enumerate(y.columns):
            if verbose: print(f' -in col {i}:'.ljust(pad), col)

            if not col in y.columns:
                if verbose: print('col not found in y\n')
                continue
            
            if verbose: print(' -- x_val:'.ljust(pad), x.loc[row, col])
            if verbose: print(' -- y_val:'.ljust(pad), y.loc[row, col])

            if y.loc[row, col] == x.loc[row, col]:
                if verbose: print('ok\n')
                df_out.loc[row, col] = '-'
            else:
                if verbose: print('NOT EQUAL\n')

    print(df_out)


def show_row_diffs(x, y):

    cell_max = 12

    x_lines = x.to_string().split('\n')

    print("    " + x_lines[0])
    print("    " + x_lines[1])

    for i, row in enumerate(x.index):
        attrs = []
        if row in y.index:
            tag = "    "
        else:
            attrs.append('bold')
            tag = "+++ "

        cprint(tag + x_lines[i+2], attrs=attrs)





def make_acc_objects(dfs_dict):
    """
    Generate new tx files and parsers from input dict of dfs

    Finds accounts by looking for acc* at start of keys.
    Finds parsers by keys ending *parser.
    Finds new txs by keys ending *new_txs.

    Returns dict of accounts, each with a parser (if present) and a list of
    new_txs files.  Eg

    {acc1: 'parser':   <the actual parser dict for acc1>,
           'new_txs':  [ acc1_new_txs_df1, acc1_new_txs_df2, .. ],

    acc2: 'parser':   <the actual parser dict for acc2>,
           'new_txs':  [ acc2_new_txs_df1, acc2_new_txs_df2, .. ],

    """

    objects = {key: dfs_dict['input'][key] for key in dfs_dict['input']
                                         if key.startswith('acc')}

    account_names = set([x.split('_')[0] for x in objects])

    accounts = {}

    for name in account_names:
        accounts[name] = {'new_txs': {}, 'parser': {}}

        accounts[name]['new_txs'] = {k: objects[k] for k in objects
                                         if k.startswith(name)
                                         and k.endswith('new_txs')}

        parsers = [k for k in objects if k.startswith(name)
                                      and k.endswith('parser')]

        if len(parsers) > 1:
            print('multiple parsers found for', name, ':')
            print(parsers)
            print('using last:', parsers[-1])

        if len(parsers):
            json_out = {}
            df = objects[parsers[-1]]
            for col in df.columns:
                val = df.loc[1, col]
                if val != 'None':
                    json_out[col] = df.loc[1, col]

            accounts[name]['parser'] = make_parser(**json_out)

    return accounts


def make_dbs_from_master_dfs(dfs_dict):
    """
    Prepares known dbs from passed dict of dfs, 
    loaded by make_dfs_from_master_xls.

    Other structures are ignored
    """

    dict_out = {}

    for stage in dfs_dict:
        dict_out[stage] = {}

        for db in dfs_dict[stage]:

            df = pd.DataFrame(dfs_dict[stage][db])

            if db == 'tx_db':
                df = fill_out_test_tx_db(df)
                df['net_amt'] = df['net_amt'].astype(float)
                dict_out[stage][db] = df

            elif db.endswith('_db'):
                dict_out[stage][db] = df.set_index('_item')

    return dict_out



def make_dfs_from_master_xls(master_xls_path):
    """
    Parses an xlsx, extracting matrix of dfs defined in row 1 and col 1.

    Returns a dict with first level keys corresponding to row 1 labels,
    second level keys being col 1 labels
    """

    raw_df = pd.read_excel(master_xls_path, index_col=0)
    # return raw_df

    row_plan = make_spans(raw_df.index)
    col_plan = make_spans(raw_df.columns)

    out = {}

    for col in col_plan:
        out[col[0]] = {}
        
        for row in row_plan:

            if row[0] == 'explanation':
                continue

            # make a df of the defined area
            df_area = raw_df.iloc[row[1]:row[2], col[1]:col[2]]
            
            # set columns
            df_area.columns = df_area.iloc[0]
            df_area = df_area.dropna(how='all', axis=1)

            # stop if completely empty
            if all(pd.isna(df_area.columns)):
                continue

            # edge case of empty df (cols, but no rows)
            if all(pd.isna(df_area.iloc[0])):
                out[col[0]][row[0]] = pd.DataFrame(columns=df_area.columns)
                continue
                   
            # tidy the rows
            df_area = df_area.reset_index(drop=True)
            df_area = df_area.iloc[1:]
            df_area = df_area.dropna(how='all', axis=0)
            out[col[0]][row[0]] = df_area

    return out


def make_spans(series):
    """
    Auxilary function for make_dbs_from_master().

    For an input series with values interspersed by np.nans or 'Unnamed: ' 
    (i.e. empty cells in loaded xls or csv), return a list of tuples with:
        (value, start_index, end_index)

    where start_index is the index of value, and end_index is the index
    of the next value, or the end of the series
    """

    tags = [(tag, i) for i, tag in enumerate(series)
                if not (pd.isna(tag) or tag.startswith('Unnamed: '))]

    spans = []

    for i, tag in enumerate(tags):
        if i == len(tags) - 1:
            span_end = len(series)
        else:
            span_end = tags[i + 1][1] - 1

        spans.append((*tag, span_end))

    return spans


def fill_out_test_tx_db(partial_tx_db):
    """
    For a partial tx_db with cols ['_item', 'accX', 'accY'],
    add the rest
    """

    essential_cols = ['_item', 'accX', 'accY']
    nonessential_cols = ['net_amt', 'id', 'mode', 'source']
    df = partial_tx_db

    if not 'date' in df.columns:
        df['date'] = pd.date_range(start='1/1/2000', periods=len(df))

    df = df.set_index('date', drop=True)

    if not 'net_amt' in df.columns:
        df['net_amt'] = [get_net_amt_hash(x) for x in range(len(df))]

    if not 'id' in df.columns:
        df['id'] = list(range(10, 10 + len(df)))

    df['id'] = df['id'].astype(int)

    if not 'mode' in df.columns:
        df['mode'] = 'not set'

    if not 'source' in df.columns:
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

