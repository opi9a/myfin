import pandas as pd
import os

from finance.categorise import categorise
from finance.load_new_txs import load_new_txs
from finance.Account import Account 

def setup_dbs():
    # new_tx
    tx = pd.DataFrame([
        ['13/01/2003','not findable', 10, 'n/a'],
        ['14/01/2003','not findable', 10, 'n/a'],
        ['13/01/2004','absent categ', 'n/a', 99],
        ['14/01/2004','absent categ', 'n/a', 99],
        ['13/01/2005','item1', 'n/a', 20],
    ],
    columns=['t_date', 't_item', 't_credit', 't_debit'])
    new_items = ['oldunknown1', 'known1', 'oldfuzzy1', 'new fuzzy item', 'newunknown']
    tx['t_item'] = new_items
    tx.to_csv('new_tx.csv', index=False)
    
    # knowns
    cols = {'_item': ['known1','known1'],
            'accX':  ['acc3','acc2'],
            'accY':  ['cat3','cat2'],
           }
    knowns = pd.DataFrame(cols)
    knowns = knowns.set_index('_item') 
    knowns.to_csv('cat_db.csv')

    # unknowns
    cols = {'_item': ['oldunknown1','oldunknown2'],
            'accX':  ['acc1','acc2'],
            'accY':  ['unknown','unknown'],
           }
    unknowns = pd.DataFrame(cols)
    unknowns = unknowns.set_index('_item') 
    unknowns.to_csv('unknowns.csv')

    # fuzzy
    cols = {'ITEM': ['oldfuzzy1','oldfuzzy2', 'oldfuzzy3'],
            'accX':  ['acc1','acc2','acc3'],
            'match_ITEM':  ['oldfuzmatch1','oldfuzmatch2','oldfuzmatch3'],
            'match_accX':  ['acc1','acc2','acc3'],
            'match_accY':  ['cat1','cat2','cat3'],
            'match_id':  [111,112,113],
            'status':  'unconfirmed',
           }
    fuzzy_db = pd.DataFrame(cols)
    fuzzy_db = fuzzy_db.set_index('ITEM')
    fuzzy_db.to_csv('fuzzy_db.csv')

    # the tx_db
    cols = {'accX':  ['acc1','acc2'],
            'accY':  ['cat1','cat2'],
            'net_amt':  [10,20],
            'ITEM': ['FUZZY item1','NOT FZ FINDABLE'],
            '_item': ['fuzzy item1','not fz findable'],
            'id':  [101,102],
            'mode':  [1,1],
           }
    ind = pd.DatetimeIndex(start=pd.datetime(2003,1,13),
                           periods=len(unknowns), freq='D')
    ind.name= 'date'
    tx_db = pd.DataFrame(cols, index=ind)
    tx_db.to_csv('tx_db.csv', date_format="%d/%m/%Y")

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


# MAIN SEQUENCE

def test_main(return_dfs=False):

    # set up the initial state
    df = make_target_df()
    print('df made\n', df)

    init_csvs(df)
    print("\ntxdb before\n", pd.read_csv(txdb))

    assert pd.read_csv(txdb).shape == (1,7)
    assert pd.read_csv(new_tx1).shape == (5,4)
    assert pd.read_csv(new_tx2).shape == (3,3)

    # run the function to import the transactions
    load_output = load_new_txs(raw_tx_path=new_tx1,
                              txdb_file=txdb,
                              account_name='acc1',
                              parser=parser)
    print('output of load_new_txs():', load_output)

    # TODO now is the time to check for any new accounts to create


    generated_df = pd.read_csv(txdb, index_col='date',
                       parse_dates=True, dayfirst=True)

    print("\ntxdb after loading\n", generated_df)

    # assert False
    assert generated_df.equals(df)

    # make an account and return a view
    acc = Account('amphibiana', generated_df, parser)

    assert acc.view().shape == (2, 6)

    # change the category map
    categ_map_df = pd.read_csv(categ_map, index_col='ITEM')

    # change one assignation
    categ_map_df.loc['changelly', 'category'] = 'crypto'

    # add an unknown, which should be ignored
    categ_map_df.loc['init_item', 'category'] = 'unknown'

    # write back to disk
    categ_map_df.to_csv(categ_map_1)

    # now implement the recategorisation and test / assert
    recat_df = recategorise(generated_df, categ_map_1,
                            ufunc=True, return_df=True)

    print('\nrecat df\n', recat_df)
    assert recat_df.loc[recat_df['ITEM'] == 'changelly', 'to'].values \
                                                            == 'crypto'
    assert recat_df.shape == generated_df.shape

    if return_dfs: return df, generated_df, recat_df

    # assert False 
