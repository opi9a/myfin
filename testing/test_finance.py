import pandas as pd
import os

from finance.categorise import categorise
from finance.import_tx import import_tx 

# first make the target data.  Use this to generate the raw inputs, 
# and then test them

def make_df():

    df = pd.DataFrame(columns=['date', 'from', 'to', 'amt', 'item'])
    df.loc[0] = [pd.datetime(2009, 1, 3), 'acc 1', 'init_acc', 11.11, 'init_item']

    df = df.set_index('date')

    df.loc[pd.datetime(2016, 12, 25)] = ['acc 1', 'amphibiana', 22.22, 'newt cuffs']
    df.loc[pd.datetime(2015, 11, 24)] = ['acc 1', 'amphibiana', 33.33, 'newt ruffs']
    df.loc[pd.datetime(2014, 10, 23)] = ['cafe income', 'acc 1', 44.44, 'tea sales']

    return df


# define some file paths
# def set_paths():
txdb='txdb.csv'
categ_map='categ_map.csv'
new_tx='new_tx.csv'
new_acc_name='new_acc' # at some point need name for accoun
accounts='accounts.pkl'

# need a parser 
parser = dict(input_type = 'credit_debit',
              date_format = "%d/%m/%Y", 
              mappings = {
                  'date': 't_date',
                  'item': 't_item',
                  'debit_amt': 'debit',
                  'credit_amt': 'credit',
              })


def init_state(df):
    
    # first delete any extant files
    if os.path.isfile(txdb): os.remove(txdb)
    if os.path.isfile(categ_map): os.remove(categ_map)
    if os.path.isfile(new_tx): os.remove(new_tx)
    if os.path.isfile(accounts): os.remove(accounts)

    # 1. save the stub of tx database to disk
    df.iloc[0:1].to_csv(txdb, date_format="%d/%m/%Y")
    print("Tx database stub written:\n", pd.read_csv(txdb), end="\n")
    df = df.iloc[1:]

    # 2. make an input tx csv
    # want to test different import structures, and categories
    #  (at least one income and one outgoing)
    # do the import structures by using full set of possible columns 
    # (only desired ones are selected anyway)
    # do categories by having rows so that there is at least one item
    #  that gets found, one that can't be, and one fuzzy matchable

    # change date format
    # change column labels for date, item
    # make colums for debit, credit, net_amt


    df = df.copy().drop(['from', 'to'], axis=1).reset_index()
    df['date'] = df['date'].apply(lambda x:
                              pd.datetime.strftime(x, parser['date_format']))
    df.columns = ['t_' + x for x in df.columns]

    df = df.rename(columns = {'t_amt':'net_amt'})
    df['debit'] = df['net_amt']
    df['credit'] = 'n/a'
    df['net_amt'] *= -1


    # tea sales row is income - swap credit/debit and make net_amt positive
    row = df.loc[df['t_item'] == 'tea sales'].copy()
    print('row is', row)
    deb_temp = row.loc[:,'debit'].copy()
    cred_temp = row.loc[:,'credit'].copy()
    row.loc[:,'credit'] = deb_temp
    row.loc[:,'debit'] = cred_temp
    df.loc[df['t_item'] == 'tea sales'] = row
    df.loc[df['t_item'] == 'tea sales','net_amt'] *= -1

    # introduce a stray space, to test stripping (currently in read_csv())
    x = " " + str(df.loc[1,'t_item'])
    df.loc[1,'t_item'] = x
    print("introduced stray space: ", "'" +  df.loc[1,'t_item'] + "'")

    df.to_csv(new_tx, index=False)


    # 3. make a category map
    with open(categ_map, 'w') as f:
       f.write("item,category\n")
       f.write("Newt Cuffs,amphibiana\n")
       f.write("tea sales,cafe income\n")
       f.write(" init_item,init_acc\n")


# MAIN SEQUENCE

def test_main():

    # set up the initial state
    df = make_df()
    print('df made\n', df)

    init_state(df)
    print("txdb before\n", pd.read_csv(txdb))

    # run the function to get the imported txs
    imported_tx = import_tx(new_tx, 'acc 1', parser, categ_map)

    # save to the tx file (what happened to stub??)
    imported_tx.to_csv(txdb, mode="a", header=False)

    print("txdb after\n", pd.read_csv(txdb))

    generated_df = pd.read_csv(txdb, index_col='date',
                       parse_dates=True, dayfirst=True)

    assert generated_df.equals(df)



"""
STATE AFTER LOAD ACCOUNT
-> txdb.csv categ_map.csv accounts.pkl(?) updated
    - transactions processed and appended to tx_db
        - cols renamed and selected
        - categories assigned
        - amounts coerced to amount from/to
        - given uid
    - any new category mappings added to categ_map
    - any new accounts added to accounts
    - transactions sorted by date
    - with / without fuzzy search?

    -> either check these asserts directly / individually,
       or compare resulting files / structures to 'correct' versions
       (may as well check loaded df versions as that's how will be used)

scaling considerations: may want to
- add accounts
- generate views by time period (binned or cumulative / rolling)
- generate rules for future transactions (fut_tx_db)
- do stuff with asset value growth
- look up asset prices

initial setup
- input tx csv on disc
  - accomomodate different structures, deb_cred / net_amt / from_to
  - best to do this with one csv having many columns for all the different
    structures, as only the relevant ones should be selected
- category map with one or two existing mappings

categorise() output / state effect

- return a list of categories for input items
-> assert list of categories returned == target list of categories

- add rows to the category map according to k
-> target outputs reqd:
    - expected category list
    - category map csv has correct rows appended
    - (category map csv test lookup?)
-> assert new category map csv == target

import_tx output / state effect
- return df with correct columns and values for all input rows
- add rows to the category map according to k [as above]

"""



#--- SET UP TEST VARIABLES ---

## generate test csvs for import (to work with all versions - debit_credit etc)
#t_dates =  ['20-01-2016',
#            '18-04-2014',
#            '2-11-2017']

#t_items =  ['TEA CHEST SALES',
#            'Newt Ruffs',
#            'playboy subs']

#t_debit =  ['n/a',
#            '40.66',
#            '33.62']
#t_credit =  ['55.55',
#            'n/a',
#            'n/a']

#t_net_amt =  ['55.55',
#            '-40.66',
#            '-33.62']

#pd.DataFrame(dict(t_dates   = t_dates,
#                  t_items   = t_items,
#                  t_debit   = t_debit,
#                  t_credit  = t_credit,
#                  t_net_amt = t_net_amt)).to_csv('test_txs.csv', 
#                                                  index=False)

## now need to define the outputs:

## little function to generate a category map csv

#def make_categ_map(path='categs.csv'):

#    # first get rid of existing versions of the file
#    if os.path.isfile(path): os.remove(path)

#    with open(path, 'w') as f:
#        f.write('Newt Cuffs,amphibia accessories\n')
#        f.write('Tea Chest Sales,beverage income\n')

## TODO define expected results of updating category map
#new_categs = {}

#new_categs['normal'] = ['beverage income',
#                        'unknown',
#                        'unknown']  

## note there will be four categories after fuzzy search, 
## as both items (the original and fuzzed) will be included
#new_categs['fuzzy'] = ['beverage income',
#                       'amphibia accessories',
#                       'unknown']  



##--- HELPER FUNCTIONS ---

#def _categorise(fuzziness, categs_path='categs.csv'):
        
#    # generate the test csv file
#    make_categ_map()

#    # set fuzzy flag
#    fuzzymatch = True if fuzziness == 'fuzzy' else False
#    print(fuzzymatch)

#    # call the function        
#    categs = categorise(t_items, categs_path, fuzzymatch=fuzzymatch)

#    print("Categories returned from categorise:", categs)
#    print("Categories to compare", new_categs[fuzziness])

#    # check expected categories have been returned
#    assert(categs == new_categs[fuzziness])

#    # check updated category map
#    new_categ_map = pd.read_csv(categs_path, header=None)
#    print("new category map loaded\n", new_categ_map)
#    assert(list(new_categ_map[0] == t_items))
#    assert(list(new_categ_map[1] == new_categs[fuzziness]))


##--- ACTUAL TEST FUNCTIONS ---
    
#def test_categorise_normal():
#    _categorise('normal')
    
#def test_categorise_fuzzy():
#    _categorise('fuzzy')
    
#def test_load_tx():
#    pass
