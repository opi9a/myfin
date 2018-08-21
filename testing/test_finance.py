import pandas as pd
import os
from pprint import pprint
import pytest

import finance.load_new_txs as lntx

@pytest.fixture
def tx_df_fx():
    lines = []
    columns=['t_date', 't_item', 't_credit', 't_debit', 't_balance']

    lines.extend ([
       ['13/01/2003','oldunknown', 100, 'n/a', 101.0],
       ['14/01/2003','known', 100, 'n/a', 201.0],
       ['13/01/2004','oldfuzzy', 'n/a', 99, 102.0],
       ['14/01/2004','new fuzzy item', 'n/a', 99, 3.0],
       ['13/01/2005','newunknown', 'n/a', 20, -17.0],
    ])

    tx = pd.DataFrame(data = lines, columns=columns)

    return tx

@pytest.fixture
def parser_fx():
    parser = lntx.make_parser(date='t_date', ITEM='t_item',
                              credit_amt='t_credit',
                              debit_amt='t_debit',
                              balance='t_balance',
                             )
    return parser


# currently this is set up to demo teardowns gratuitously
@pytest.fixture
def x_fx():
    # create a file to save, for tearing down later
    xdf = pd.DataFrame({'x':1}, index=['y'])
    xdf.to_csv('test_file_to_teardown.csv')
    print('dumped a file')
    print(os.listdir())

    # yield, rather than return
    yield 'yielding from x_fx'

    # everything after the yield statement is executed at teardown
    os.remove('test_file_to_teardown.csv')
    print('removed it')
    print(os.listdir())

#------------------------------------------------------------------------------

def test_main_seq(tx_df_fx, parser_fx):

    # formatting raw txs
    df = lntx.format_new_txs(tx_df_fx, 'test', parser_fx)
    assert list(df.columns) == ['date', 'ITEM', '_item',
                                'net_amt', 'balance']
    assert pd.core.dtypes.common.is_datetime64_any_dtype(df.date)

    return df

    # checking balance continuity
    bal_cont = lntx.balance_continuum(df)
    assert sum(bal_cont) == 0

    # now delete a field, should have a non-zero
    bal_cont1 = lntx.balance_continuum(df.drop(2))
    assert list(bal_cont1) == [0,-99,0]


#------------------------------------------------------------------------------

def test_format_txs(tx_df_fx, parser_fx):
    df = lntx.format_new_txs(tx_df_fx, 'test', parser_fx)
    assert list(df.columns) == ['date', 'ITEM', '_item',
                                'net_amt', 'balance']
    assert pd.core.dtypes.common.is_datetime64_any_dtype(df.date)
    # assert 0


def test_balance_continuum(tx_df_fx, parser_fx):
    """When passed a tx_df with 'balance' column, check that it is 
    self-consistent as a continuous sequence of transactions.
    """

    # make a formatted df which should pass
    df = lntx.format_new_txs(tx_df_fx, 'test', parser_fx)
    
    bal_cont = lntx.balance_continuum(df)
    assert sum(bal_cont) == 0

    # now delete a field, should have a non-zero
    bal_cont1 = lntx.balance_continuum(df.drop(2))
    assert list(bal_cont1) == [0,-99,0]


# new, with empty option, doesnt pick up new fuzzies
def setup_dbs(empty=False, proj_dir_reqd=True, clean_dir=True):
    """Sets up a full complement of databases for testing, over-writing
    any existing files by default:
        - tx_db      : the main database
        - new_tx     : the transactions to load
        - cat_db     : items previously assigned to categories
        - unknowns_db: items previously designated unknown
        - fuzzy_db   : itemps previously assigned with a fuzzy match

    Also generates a parser.pkl file to work with the new_tx.csv

    Pass empty=True to get empty versions of the basic csvs:
        tx_db, cat_db, fuzzy_db, unknowns_db

    Will only work in a directory containing string 'proj', to stop
    accidentally polluting other folders. Override this behaviour by
    changing proj_dir_reqd flag.

    Overwrites existing files by default.
    """

    if proj_dir_reqd and 'test' not in os.path.basename(os.getcwd()):
        print('not in a proj directory')
        return 1

    if clean_dir:
        for f in os.listdir():
            print('removing', f)
            os.remove(f)


    # new_tx - only make if not passing 'empty' flag
    if not empty:
        lines = []
        columns=['t_date', 't_item', 't_credit', 't_debit']

        lines.extend ([
           ['13/01/2003','oldunknown', 10, 'n/a'],
           ['14/01/2003','known', 10, 'n/a'],
           ['13/01/2004','oldfuzzy', 'n/a', 99],
           ['14/01/2004','new fuzzy item', 'n/a', 99],
           ['13/01/2005','newunknown', 'n/a', 20],
        ])

        tx = pd.DataFrame(data = lines, columns=columns)
        tx.to_csv('new_tx.csv', index=False)

    
    # use these columns as base for all ref dbs
    db_columns=['_item', 'accX', 'accY']

    # knowns - only fill if not passing 'empty' flag
    lines = []
    if not empty:
        lines.extend ([
        ['known','acc3','cat3'],
        ['known','acc2','cat4'],
        ['new fuzzy to find','acc2','cat5'],
        ])
    tx = pd.DataFrame(data = lines, columns=db_columns)
    tx = tx.set_index('_item')
    tx.to_csv('cat_db.csv', index=True)

    # unknowns - only fill if not passing 'empty' flag
    lines = []
    if not empty:
        lines.extend ([
        ['oldunknown','acc2','unknown'],
        ['oldunknown','acc2','unknown'],
        ])
    tx = pd.DataFrame(data = lines, columns=db_columns)
    tx = tx.set_index('_item')
    tx.to_csv('unknowns_db.csv')


    # fuzzy - only fill if not passing 'empty' flag
    lines = []

    if not empty:
        lines.extend ([
            ['oldfuzzy', 'acc1', 'cat5', 'unconfirmed'],
            ['oldfuzzy2', 'acc2', 'cat6', 'unconfirmed'],
            ['oldfuzzy3', 'acc3', 'cat7', 'unconfirmed']
                    ])
    fuzzy_cols = db_columns + ['status']
    tx = pd.DataFrame(data = lines, columns=fuzzy_cols)
    tx = tx.set_index('_item')
    tx.to_csv('fuzzy_db.csv')

    # the tx_db - always empty
    lines = []
    columns=['accX', 'accY', 'net_amt', 'ITEM', '_item', 'id', 'mode']

    ind = pd.DatetimeIndex(start=pd.datetime(2003,1,13),
                           periods=len(lines), freq='D')
    ind.name= 'date'
    tx = pd.DataFrame(data = lines, columns=columns, index=ind)
    tx.to_csv('tx_db.csv', date_format="%d/%m/%Y")


    # need a parser - only make if not passing 'empty' flag
    if not empty:
        parser = dict(input_type = 'credit_debit',
                      date_format = "%d/%m/%Y", 
                      map = {
                          'date': 't_date',
                          'ITEM': 't_item',
                          'debit_amt': 't_debit',
                          'credit_amt': 't_credit',
                         })

        pd.to_pickle(parser, 'parser.pkl')


def print_dir(pkls=True):
    """Reads and prints all .csv and .pkl files in a directory.
    (pkls must be dict).
    """
    for f in os.listdir():
        print("-"*50, end="\n")
        print(f, end="\n\n")
        if f.endswith('csv'):
            df = pd.read_csv(f)
            index_col = df.columns[0] 
            print(df.set_index(index_col), end="\n\n")
        if f.endswith('pkl'):
            if pkls:
                pprint(pd.read_pickle(f))


"""
First make a target df for the expected result after processing.

Use this to back-create the raw inputs for the functions and tests. Those are:
    1. an initial tx_db.csv, with one or more categorisations made
    2. a new_tx1.csv in 'credit_debit' form, with categorisations reqd
        - some fuzzy 
        - some negative flows
    3. a new_tx2.csv in 'net_amt' form

Then run load_new_txs() for each new_tx.csv

Test that df generated is same as the target df.

Change the categorisation of one ITEM and call recategorise() or similar

"""

# first define some file paths
txdb='txdb.csv'
new_tx1='new_tx1.csv'
new_tx2='new_tx2.csv'
new_acc_name='new_acc' # at some point need name for accoun
accounts='accounts.pkl'

def make_target_df():
    columns=[
 'date',      'accX', 'accY', 'amt', 'ITEM',     'id','mode']

    lines = [
# first what will be the initial txdb, to which others will add, but also
# will serve as the initial category map to look others up.
# So want to establish an initial ITEM->category mapping that can 
# then also be used to test fuzzy mapping, with a slightly different ITEM.
["13/01/2001",'acc1', 'cat1',  1.00, 'item1 norm',  1, -1],# initial txdb

# Simple new tx, looks up cat1 mapping directly 
["13/01/2005",'acc1', 'cat1',  2.00, 'item1 norm',  2,  1],# 

# A negative flow
["13/01/2006",'acc1', 'cat2', -3.00, 'map to cat2', 3, -1],#   

# Will test for handling a doublet of transactions
["13/01/2002",'acc1', 'acc2',  4.00, 'item1 norm',  4,  1],#   
["13/01/2002",'acc2', 'acc1', -4.00, 'item1 norm',  5,  1],#   

# A fuzzy lookup for cat1
["13/01/2003",'acc1', 'cat1',  6.00, 'item1 fuzz',  6,  1],#   
["13/01/2007",'acc1', 'cat2',  7.00, 'map to cat2', 7,  3],#   

# Some transactions for acc2
["13/02/2007",'acc2', 'cat2', 17.00, 'item1 norm', 8,  1],#   
["13/02/2007",'acc2', 'cat2', 27.00, 'item1 fuzz', 9,  1],#   
    ] 

    return pd.DataFrame(data=lines, columns=columns).set_index('date')


# will need a parser 
parser = dict(input_type = 'credit_debit',
              date_format = "%d/%m/%Y", 
              mappings = {
                  'date': 't_date',
                  'ITEM': 't_item',
                  'debit_amt': 't_debit',
                  'credit_amt': 't_credit',
              })

def init_csvs(df):
    """Creates three csv files from an input txdb df:
        - a 'stub' txdb
        - a new_tx1.csv with acc1 txs in 'credit_debit' format
        - a new_tx2.csv with acc2 txs in 'net_amt' format

    """

    # 0. delete any extant files
    if os.path.isfile(txdb): os.remove(txdb)
    if os.path.isfile(new_tx1): os.remove(new_tx1)
    if os.path.isfile(new_tx2): os.remove(new_tx2)
    # if os.path.isfile(accounts): os.remove(accounts)

    # first save the stub used for the txdb
    df.iloc[0:1,:].to_csv(txdb)

    # make a copy of acc1 txs, and drop the line that's already been used
    new_tx1_df = df[df['accX'] == 'acc1'].iloc[1:,:].copy()

    # make columns for tx going in and out of the account
    new_tx1_df['debit'] = new_tx1_df.loc[new_tx1_df['amt'] > 0, 'amt']
    new_tx1_df['credit'] = new_tx1_df.loc[new_tx1_df['amt'] < 0, 'amt'] *-1

    # select reqd columns and rename, so they have to be renamed when importing
    new_tx1_df = new_tx1_df[['ITEM', 'debit', 'credit']].reset_index()
    new_tx1_df.columns = ['t_'+x for x in new_tx1_df.columns]

    # save to disk
    new_tx1_df.to_csv(new_tx1, index=False)

    # make a copy of acc2 txs
    new_tx2_df = df[df['accX'] == 'acc2'].copy()

    # select and rename columns
    new_tx2_df = new_tx2_df[['ITEM', 'amt']].reset_index()
    new_tx2_df.columns=[['t_date','t_item', 't_net_amt']]

    new_tx2_df.to_csv(new_tx2, index=False)


# # MAIN SEQUENCE

# def test_main(return_dfs=False):
#     # this needs redeveloping, so just head it off here for now
#     assert True
#     return

#     # set up the initial state
#     df = make_target_df()
#     print('df made\n', df)

#     init_csvs(df)
#     print("\ntxdb before\n", pd.read_csv(txdb))

#     assert pd.read_csv(txdb).shape == (1,7)
#     assert pd.read_csv(new_tx1).shape == (5,4)
#     assert pd.read_csv(new_tx2).shape == (3,3)

#     # run the function to import the transactions
#     load_output = parse_new_txs(raw_tx_path=new_tx1,
#                               txdb_file=txdb,
#                               account_name='acc1',
#                               parser=parser)
#     print('output of load_new_txs():', load_output)

#     # TODO now is the time to check for any new accounts to create


#     generated_df = pd.read_csv(txdb, index_col='date',
#                        parse_dates=True, dayfirst=True)

#     print("\ntxdb after loading\n", generated_df)

#     # assert False
#     assert generated_df.equals(df)

#     # make an account and return a view
#     acc = Account('amphibiana', generated_df, parser)

#     assert acc.view().shape == (2, 6)

#     # change the category map
#     categ_map_df = pd.read_csv(categ_map, index_col='ITEM')

#     # change one assignation
#     categ_map_df.loc['changelly', 'category'] = 'crypto'

#     # add an unknown, which should be ignored
#     categ_map_df.loc['init_item', 'category'] = 'unknown'

#     # write back to disk
#     categ_map_df.to_csv(categ_map_1)

#     # now implement the recategorisation and test / assert
#     recat_df = recategorise(generated_df, categ_map_1,
#                             ufunc=True, return_df=True)

#     print('\nrecat df\n', recat_df)
#     assert recat_df.loc[recat_df['ITEM'] == 'changelly', 'to'].values \
#                                                             == 'crypto'
#     assert recat_df.shape == generated_df.shape

#     if return_dfs: return df, generated_df, recat_df

#     # assert False 
