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


def db_compare(test, target, db_name=None,
                   cols_to_ignore=['id', 'source', 'mode'],
                   index_cols=None,
                   assertion=False):
    """
    Compares two dataframes.

    First naively applies target.equals(test), returns True
    (and asserts True) if True.

    If not, compare columns and indexes.

    Finally compare common core (common index and columns)

    To make unique indexes probably want to set indexes to eg
    ['date', '_item', 'accX']

    Passing cols_to_ignore affects only equality test - the cols will still
    be printed and compared if dfs not equal
    """

    # get rid of pesky nans which compare unequal
    test = test.copy().fillna("BLANK").sort_index()
    target = target.copy().fillna("BLANK").sort_index()

    # make sure columns same 
    if set(test.columns) != set(target.columns):
        print('test and target have different columns')
        return

    # apply index cols if reqd
    if index_cols is not None:
        test = test.reset_index().set_index(index_cols, drop=True)
        target = target.reset_index().set_index(index_cols, drop=True)

    # get columns in same order (based arbitrarily on test)
    target = target[test.columns]

    if db_name is not None:
        print_title(db_name.upper())

    if cols_to_ignore:
        print('ignoring columns', cols_to_ignore, end=" ")
    else:
        print('ignoring no columns', end=" ")

    print(target.shape, "vs", test.shape, end=": ")

    # simple equality test
    cols_to_try = test.columns.difference(cols_to_ignore)
    if target[cols_to_try].equals(test[cols_to_try]):
        cprint('dbs equal by df.equals()', color='green', attrs=['bold'])
        if assertion:
            assert True
        return True

    cprint('NOT EQUAL', color='red', attrs=['bold'])

    print_title(str(db_name) + ':  INEQUALITY ANALYSIS')
    print('\ntest df:')
    print(test)
    print('\ntarget df:')
    print(target)

    # COMPARE INDEXES
    if tuple(test.index) != tuple(target.index):
        print_title(str(db_name) + ':  INDEX DIFFS')
        print('\nNon-identical indexes')
        diff_indexes(test, target)
    else:
        print('indexes are the same')
    # Print df comparisons / differences
    print_title(str(db_name) + ':  DF COMPARISONS')

    # mask - NB a superset / union with all rows and columns
    mask = test[cols_to_try].eq(target[cols_to_try])

    # print the result of eq() but using '-' and 'X' markers
    mask_diff = mask.copy()
    mask_diff = mask_diff.where(mask, other='X')
    mask_diff = mask_diff.where(~mask, other='-')
    print('\nComparison over union')
    print(mask_diff)

    #call diffs func for row-by-row comparison - only if unique indices
    if test.index.is_unique and target.index.is_unique:
        print_title(str(db_name) + ':  TEST')
        print()
        show_df_diffs(test[cols_to_try], target[cols_to_try])
        print_title(str(db_name) + ':  TARGET')
        print()
        show_df_diffs(target[cols_to_try], test[cols_to_try])
    else:
        print('\nNot comparing row-by-row as indices not both unique')

    print_title()

    if assertion:
        assert False

    return False


def strftime_date_index(df, strf_format='%d-%m-%y'):
    """
    Converts a level of a multi-index labelled 'date' to strings
    using strftime.
    """

    orig_names = df.index.names

    df = df.reset_index()
    df['date'] = df['date'].apply(lambda x: x.strftime(strf_format))

    return df.set_index(orig_names)


def diff_indexes(df1, df2):
    """
    Compare each, highlight differences
    """

    pad = 50
    ind1 = tuple(strftime_date_index(df1).index)
    ind2 = tuple(strftime_date_index(df2).index)

    print('\nTEST'.ljust(pad) + 'TARGET')

    # get superset
    superset = sorted(list(set(ind1).union(set(ind2))), key=lambda x: x[0])

    out = {}

    for elem in superset:
        counts = {'ind1': ind1.count(elem), 'ind2': ind2.count(elem)}

        while max(counts.values()):
            for ind in counts:
                if counts[ind]:
                    counts[ind] -= 1
                    out.setdefault(ind, []).append(", ".join(elem))
                else:
                    out.setdefault(ind, []).append(None)

    for i in range(len(out['ind1'])):
        if out['ind1'][i] == out['ind2'][i]:
            color = None
        else:
            color = 'red'

        for ind in out:
            if out[ind][i] is None:
                cprint(('-' * (pad - 9)).ljust(pad), color=color, end="")
            else:
                cprint(out[ind][i].ljust(pad), color=color, end="")

        print("")

def make_extended_index(df):
    """
    Returns the df with a multi-index made from the standard input
    columns ['_item', 'accX', 'date'].
    """

    indexes_to_add = list(df.columns.intersection(['_item', 'accX', 'date']))

    df = df.set_index(sorted(indexes_to_add), append=True).sort_index()

    index_list = list(df.index)

    return df


def show_df_diffs(x, y, verbose=False):
    """
    Attempts cell-by-cell comparison of dfs.

    Only works if row indexes are unique
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


def make_dbs_from_master_dfs(dfs_dict, index_col=None):
    """
    Prepares dbs from passed dict of dfs, 
    loaded by make_dfs_from_master_xls.

    Known dbs (eg 'tx_db', 'cat_db') processed appropriately, given 
    right index etc.

    Others given passed index_col, or left with original index.
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

            elif index_col is not None:
                dict_out[stage][db] = df.set_index(index_col)

            else:
                dict_out[stage][db] = df

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


def print_title(title_string="", attrs=None):
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

    print('\n')
    cprint("".join(["*" * bar1, title_string, "*" * bar1]), attrs=attrs)


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

