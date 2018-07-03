import pandas as pd
import os

from finance.categorise import categorise, recategorise
from finance.load_new_txs import load_new_txs 
from finance.Account import Account 

# first make the target data.  Use this to generate the raw inputs, 
# and then test them

def make_df():
    columns=[
 'date',      'accX', 'accY', 'amt', 'item',     'id','mode']

    lines = [
# first what will be the initial txdb, to which others will add, but also
# will serve as the initial category map to look others up.
# So want to establish an initial item->category mapping that can 
# then also be used to test fuzzy mapping, with a slightly different item.
["13/01/2001",'acc1', 'cat1',  1.00, 'item1 norm',  1, -1],# initial txdb

# Simple new tx, looks up cat1 mapping directly 
["13/01/2005",'acc1', 'cat1',  2.00, 'item1 norm',  2,  1],# 

# A negative flow
["13/01/2006",'acc1', 'cat2', -3.00, 'map to cat2', 3, -1],#   

# A doublet of transactions
["13/01/2002",'acc1', 'acc2',  4.00, 'item1 norm',  4,  1],#   
["13/01/2002",'acc2', 'acc1', -4.00, 'item1 norm',  5,  1],#   

# A fuzzy lookup for cat1
["13/01/2003",'acc1', 'cat1',  6.00, 'item1 fuzz',  6,  1],#   
["13/01/2007",'acc1', 'cat2',  7.00, 'map to cat2', 7,  3],#   
    ] 

    return pd.DataFrame(data=lines, columns=columns).set_index('date')


# define some file paths
txdb='txdb.csv'
new_tx='new_tx.csv'
new_acc_name='new_acc' # at some point need name for accoun
accounts='accounts.pkl'

# will need a parser 
parser = dict(input_type = 'credit_debit',
              date_format = "%d/%m/%Y", 
              mappings = {
                  'date': 't_date',
                  'item': 't_item',
                  'debit_amt': 'debit',
                  'credit_amt': 'credit',
              })


def init_state(df):
    
    # 0. delete any extant files
    if os.path.isfile(txdb): os.remove(txdb)
    if os.path.isfile(categ_map): os.remove(categ_map)
    if os.path.isfile(new_tx): os.remove(new_tx)
    if os.path.isfile(accounts): os.remove(accounts)

    # 1. save the stub of tx database to disk
    df.iloc[0:1].to_csv(txdb, date_format="%d/%m/%Y")
    print("Tx database stub written:\n", pd.read_csv(txdb), end="\n")

    # drop that row
    df = df.iloc[1:]

    # 2. make an input tx csv
    # want to test different import structures, and categories
    
    # do the import structures by using full set of possible columns 
    # (only desired ones are selected anyway)
    # do categories by having rows so that there is at least one item
    #  that gets found, one that can't be, and one fuzzy matchable

    # change date format
    # change column labels for date, item
    # make colums for debit, credit, net_amt


    df = df.copy().drop(['from', 'to', 'item_from_to'], axis=1).reset_index()
    df['date'] = df['date'].apply(lambda x:
                              pd.datetime.strftime(x, parser['date_format']))
    df.columns = ['t_' + x for x in df.columns]
    print('df columns now')

    df = df.rename(columns = {'t_amt':'net_amt'})
    df['debit'] = df['net_amt']
    df['credit'] = 'n/a'
    df['net_amt'] *= -1


    # tea sales row is income - swap credit/debit and make net_amt positive
    row = df.loc[df['t_item'] == 'tea sales'].copy()
    deb_temp = row.loc[:,'debit'].copy()
    cred_temp = row.loc[:,'credit'].copy()
    row.loc[:,'credit'] = deb_temp
    row.loc[:,'debit'] = cred_temp
    df.loc[df['t_item'] == 'tea sales'] = row
    df.loc[df['t_item'] == 'tea sales','net_amt'] *= -1

    # introduce a stray space, to test stripping (currently in read_csv())
    x = " " + str(df.loc[1,'t_item'])
    df.loc[1,'t_item'] = x
    # print("introduced stray space: ", "'" +  df.loc[1,'t_item'] + "'")

    df.to_csv(new_tx, index=False)


    # 3. make a category map
    with open(categ_map, 'w') as f:
       f.write("item,category\n")
       f.write("Newt Cuffs,amphibiana\n")
       f.write("tea sales,cafe income\n")
       f.write("init_item,init_acc\n")


# MAIN SEQUENCE

def test_main(return_dfs=False):

    # set up the initial state
    df = make_df()
    print('df made\n', df)

    init_state(df)
    print("\ntxdb before\n", pd.read_csv(txdb))

    # run the function to import the transactions
    load_new_txs(raw_tx_path=new_tx,
                 categ_map=categ_map,
                 txdb_file=txdb,
                 account_name='acc 1',
                 parser=parser)

    # TODO now is the time to check for any new accounts to create


    generated_df = pd.read_csv(txdb, index_col='date',
                       parse_dates=True, dayfirst=True)

    print("\ntxdb after x\n", generated_df)

    # assert False
    assert generated_df.equals(df)

    # make an account and return a view
    acc = Account('amphibiana', generated_df, parser)

    assert acc.view().shape == (2, 6)

    # change the category map
    categ_map_df = pd.read_csv(categ_map, index_col='item')

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
    assert recat_df.loc[recat_df['item'] == 'changelly', 'to'].values \
                                                            == 'crypto'
    assert recat_df.shape == generated_df.shape

    if return_dfs: return df, generated_df, recat_df

    # assert False 
