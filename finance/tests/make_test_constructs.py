# myfin/finance/tests/make_test_constructs.py
import pandas as pd
from hashlib import sha1

from finance.tests.test_helpers import make_parser

"""
Functions for generating test structures (dbs and account dfs etc) from 
master xlsx files.

Primordial function is make_raw_dfs_from_master_xls, which generates raw dfs
by parsing a matrix of the passed master xlsx.

Higher level functions make dbs (tx_db, unknowns_db, fuzzy_db, cat_db) or
account objects (including parsers and input tx account files.
"""


def make_acc_objects_from_master_xlsx(master_xls_path):
    """
    Generate new tx files and parsers from master xls.
    
    Calls make_dbs_from_master_xls() to get raw dfs - a dict of dfs organised
    according to matrix in master xls.

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


    raw_dfs = make_dbs_from_master_xlsx(master_xls_path)

    objects = {key: raw_dfs['input'][key] for key in raw_dfs['input']
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


def make_dbs_from_master_xlsx(master_xls_path, index_col=None):
    """
    Makes dbs from passed master_xls_path, calling make_dfs_from_master_xls.

    Known dbs (eg 'tx_db', 'cat_db') processed appropriately, given 
    right index etc.

    Others given passed index_col, or left with original index.
    """

    raw_dfs = make_raw_dfs_from_master_xls(master_xls_path)

    dict_out = {}

    for stage in raw_dfs:
        dict_out[stage] = {}

        for db in raw_dfs[stage]:

            df = pd.DataFrame(raw_dfs[stage][db])

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


def make_raw_dfs_from_master_xls(master_xls_path):
    """
    Parses an xlsx, extracting matrix of dfs defined in row 1 and col 1.

    Drops columns or rows marked 'META'

    Returns a dict with first level keys corresponding to row 1 labels,
    second level keys being col 1 labels
    """

    raw_df = pd.read_excel(master_xls_path, index_col=0)

    if 'META' in raw_df.columns:
        raw_df = raw_df.drop('META', axis='columns')

    if 'META' in raw_df.index:
        raw_df = raw_df.drop('META', axis='index')

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

    df['id'] = df['id'].fillna(0)
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
