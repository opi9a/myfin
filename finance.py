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
    """Import raw transactions and return a tx_df in standard format,
    with date index, and columns: from, to, amt

    TODO:
        - add unique ID field
        - sort columns nicerly
        - parse date and make index
        - categorise from and to cols for 'from_to' type
        - append to any existing past tx_df (and sort etc)
        - trigger account creation for new categories

    file         : the path of the raw transaction csv file

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns
                   
    parser       : dict with instructions for processing the raw tx file
                    - 'input_type' : 'from_to', 'credit_debit' or 'net_amt'
                    - 'mapping'    : dict of mappings for column labels
                                     (new labels are keys, old are values)

                                     - must contain mappings to all reqd cols

    accounts     : the current list of account instances, from which tx 
                   parsers can be retrieved [MAYBE - NOT CURRENTLY USED]

    categ_map    : csv file containing known mappings from 'item' to 
                   category

    """

    raw_df = pd.read_csv(file, parse_dates=[parser['mappings']['date']])

    # select only the columns reqd
    raw_df = raw_df[list(parser['mappings'].values())]

    # map to the standard labels
    raw_df.columns = parser['mappings'].keys()

    # unless already in 'from_to', do the conversion
    if parser['input_type'] != 'from_to':

        # first, from 'credit_debit' to 'net_amt'
        if parser['input_type'] == 'credit_debit':
            raw_df['net_amt'] = raw_df['debit_amt'].subtract(raw_df['credit_amt'], fill_value=0)
            raw_df = raw_df.drop(['debit_amt', 'credit_amt'], axis=1)

        # then to 'from_to', also assigning categories
        raw_df['category'] = categorise(raw_df['item'],
                                        new_categ_map_path='temp_new_cat_path.csv')

        raw_df[['from', 'to']] = consol_debit_credit(raw_df, account_name)
    
    raw_df['amt'] = raw_df['net_amt'].abs()
    raw_df = raw_df.drop(['category', 'net_amt'], axis=1) 
    raw_df = raw_df.set_index('date')

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

    for item in items:

        # do the lookup - NB may return 'unknown' value,
        categ = categ_map.get(item.lower(), 'not found')

        # append result to categories for output if present in categ_map
        if categ != 'not found':
            categories.append(categ)

        elif fuzzymatch:
            best_match, score = process.extractOne(item, categ_map.keys(),
                                                   scorer=fuzz.token_set_ratio)

            if score >= fuzzy_threshold:
                categories.append(categ_map[best_match])
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append(categ_map[best_match])
                print(f'Fuzzy-matched {item}, with {best_match}, scoring {score}', file='log.txt')

            else:
                categories.append('unknown')
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append('unknown')
                print(f'No fuzzy match for {item} (best score {score})', file='log.txt')
        else:
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
    
    for row in df_in.iterrows():
        if row[1].loc['net_amt'] < 0:
            df_out.iloc[row[0],0] = acc_name
            df_out.iloc[row[0],1] = row[1].loc['category']
            
    return df_out[['from', 'to']]
