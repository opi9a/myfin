import pandas as pd
import numpy as np
import os

from fuzzywuzzy import process, fuzz


# load the tx dataset

def load_tx(path=None):
    """Load the transactions data

    Replace this with a function to load everything:
        - past tx_df
        - notes json
        - list of accounts
        - future tx_df
        - (any rules about future that have to exist separately)
    """

    if path is None:
        path = "tx.pkl"

    return pd.read_pickle(path)


class Account():

    """Main class for accounting objects

    Attributes:

        unit            : eg 'gbp', 'btc'
                          (default is 'goods' for non financials)

        classification  : a hierarchy of categories above the object.
                          eg if object is fuel: 'consumption/travel'

        view            : all transactions labelled with object's name
                          - a view of the tx_df
                        TODO, options eg all or in / out only

    Methods:

        sum             : return sum of transactions
                            - optional date since
                            - optional from or to only
todo

- ensure tx_df is sorted by date always

- implement addition method to classes to return pd.concat or whatever
   (keep as views)

- support smart aggregation, so base accounts can be attributed to multiple
   higher level categories, but overlap is dealt with when aggregating

- support prod and cons account extrapolation, using eg manual rules or 
   automatic based on detected trends

- projection based on assets: metaclasses of accounts
    eg Crypto, Property. Can have separate ones eg pensions.
    Net consumption comes out of..

- store a parsing function in accounts for loading transactions from standard
    statement structure / format
    """

    def __init__(self, name, tx_df, input_type, col_mapper,
                 unit=None, classification=None):

        self.name = name
        self.classification = classification
        self.tx_df = tx_df

        if input_type not in ['credit_debit', 'net_amt', 'to_from']:

            print("""Need input_type to be one of:
                  'credit_debit', 'net_amt', 'to_from'""")

            self.input_type = None
            self.col_mapper = None

        else:
            self.input_type = input_type 
            self.col_mapper = col_mapper

        if unit == None:
            self.unit = 'goods'

        # set up some boolean filters for the account
        # - separate in and out transactions
        self._outs = (self.tx_df['from'] == self.name)
        self._ins = (self.tx_df['to'] == self.name)


        pass

    def view(self, start_date=None, end_date=None):
        """TODO
        """
        date_slice = slice(start_date, end_date, None)

        return (self.tx_df.loc[self._outs | self._ins]
                          .loc[date_slice])


    def __repr__(self):
        return self.name


def import_txs(file, account_name, parser, accounts, categ_map):
    """Define a general approach, but use specific parsers for each acc
        - stored in account object

    accounts    : the current list of account instances, from which tx 
                  parsers can be retrieved


    Input is df with bunch of cols, of which some relevant, but likely 
    with wrong labels.

    Also may not be in right structure. Note the input is likely to be 
    associated with a single account, with transactions to others.

    Ultimately want in a 'to_from' structure, with a col for each account.
    But could be in a 'credit_debit' form, with a column each for in and out,
    with respect to the particular account, or a 'plus_minus' form with a
    single column but positive for in, negative for out.

    Also need to categorise the items to assign the partner account.

    0. Load up the input data

    """
    raw_df = pd.read_csv(file)
    """

    1. map columns
    
    Account instances to have attributes which dictate how they are 
    to be mapped.

    That is:
        an input_type identifier - 'credit_debit', 'net_amt' or 'to_from'
        a col_mapper dict with the relevant mappings of column labels

        if 'credit_debit': 'credit_amt', 'debit_amt' and 'item'

        if 'net_amt': 'net_amt' and 'item'

        if 'to_from': 'to', 'from' and 'amt'
            - 'to' and 'from' must already be categories / accounts

        and for all: 'date', 'notes'

    """
    # expand the 'mappings' element of parser - keys are OLD labels
    raw_df = raw_df.rename(columns=parser['mappings'])
    # select only the reqd columns (new labels are parser mapping values)
    raw_df = raw_df[list(parser['mappings'].values())]

    if parser['input_type'] != 'from_to':
        if parser['input_type'] == 'credit_debit':
            raw_df['net_amt'] = raw_df['debit_amt'].add(raw_df['credit_amt'], fill_value=0)
            raw_df = raw_df.drop(['debit_amt', 'credit_amt'], 1)
        raw_df['category'] = categorise(raw_df['item'], new_categ_map_path='temp_new_cat_path.csv')
        raw_df[['from', 'to']] = consol_debit_credit(raw_df, account_name)
    return raw_df

    """
        
    2. assign categories (if not 'to_from')

    3. convert to 'to_from'

        if 'credit_debit': convert to 'net_amt'

        if 'net_amt': convert to 'to_from'
        

    Then call categorise() to assign categories based on the 'items'.
        - uses 'categ_map', a mapping of item names to categories
        - this is to be stored as a csv, so it can be edited, in particular
          to assign categories to 'unknown' items

    Then generate from-to amounts
        - must generate from->to structure, when inputs are likely debit/credit

    Finally create Account instances for all from or to sources not already in 
    the list of accounts.
    """

    df = pd.read_csv(file)
    df_out = pd.DataFrame()

    account = accounts['account_name'].parser

    if parser is not None:
        df_out['date'] = df[parser['date']]

        if parser['record_type'] == 'debit_credit':
            df_out[['from'], ['to']] = consol_debit_credit(df, account_name)

        df_out['item'] = df[parser['item']]

    df_out['categories'] = categorise(df_out['item'])

    return df_out

def map_columns(df, mapper):
    pass

def categorise(items, categ_map_path='categ_map.csv', 
               new_categ_map_path=None, fuzzymatch=False, fuzzy_threshold=80):
    """Returns categories for an iterable of items, based on a lookup
    in the categ_map csv.

    Tries a fuzzy match if asked.
    
    Assign as 'unknown' if not found, AND add item to categ_map.csv 
    with 'unknown' as value.
    """

    # dict for reading in the category map from csv
    categ_map = {}  

    # list to hold the categories to return, corresponding to items
    categories = [] 

    # new assignments to append to categ_map
    new_assigns = {'new_item':[], 'new_category':[]}

    # read in csv as dict (with lower case keys for matching)
    with open(categ_map_path) as f:
        for line in f:
            a, b = line.split(',')
            categ_map[a.lower()] = b[:-1].lower() 

    print("categ_map read in:\n", categ_map)

    for item in items:

        print('\nIn item ', item)
        # do the lookup - NB may return 'unknown' value,
        categ = categ_map.get(item.lower(), 'not found')

        # append result to categories for output if present in categ_map
        if categ != 'not found':
            print('in categ found')
            categories.append(categ)

        elif fuzzymatch:
            print('in fuzzymatching')
            best_match, score = process.extractOne(item, categ_map.keys(),
                                                   scorer=fuzz.token_set_ratio)

            if score >= fuzzy_threshold:
                categories.append(categ_map[best_match])
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append(categ_map[best_match])
                print(f'Fuzzy-matched {item}, with {best_match}, scoring {score}')
                print('categories now: ', categories)

            else:
                categories.append('unknown')
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append('unknown')
                print(f'No fuzzy match for {item} (best score {score})')
        else:
            print('not found and no fuzzy attempted')
            categories.append('unknown')
            new_assigns['new_item'].append(item)
            new_assigns['new_category'].append('unknown')

    if new_assigns:

        if new_categ_map_path is not None:
            categ_map_path = new_categ_map_path

        # note: appending to csv file
        (pd.Series(new_assigns['new_category'], index=new_assigns['new_item'])
                  .to_csv(categ_map_path, mode='a'))

    return categories


def curate_categories():
    """
        Alert user and ask for assignment
        Eg in a csv file that can be changed and scanned
        Update categories dict / mapping with any changes
    """


def load_categ_map(path='categ_map.pkl'):
    return pd.read_pickle(path)

def consol_debit_credit(df_in, acc_name):
    """take a df with debit and credit cols, plus category col
    return a pair of columns with from and to
    """
    
    if 'category' in df_in.columns:
        df_out = pd.DataFrame(df_in['category'])
    else:
        df_out = pd.DataFrame(np.array(['$OUT'] * len(df_in)))
        
    
    df_out['x'] = acc_name
    df_out.columns = ['to', 'from']
    
    for i, row in enumerate(df_in.iterrows()):
        print(f"row {i}:")
        print("type of row is ", type(row))
        print("length of row is ", len(row))
        for i,entry in enumerate(row):
            print("type of entry is ", type(entry))
            
            # for j in r: print(j)
        print("")
        if pd.isnull(row[1][0]):
            df_out.iloc[row[0],0] = acc_name
            df_out.iloc[row[0],1] = row[1][2]
            
    return df_out[['from', 'to']]
