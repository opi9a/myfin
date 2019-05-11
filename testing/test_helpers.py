from pathlib import Path
import pandas as pd
from hashlib import sha1

from finance.load_new_txs import print_title


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
