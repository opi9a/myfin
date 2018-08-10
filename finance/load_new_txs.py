import pandas as pd
import numpy as np
import os
from fuzzywuzzy import fuzz, process


"""Library of functions and a main function for loading transactions
from csv files:

    1. parse the csv, using a parser dict, to give a df with standard
       columns with <parse_new_txs()>

    2. assign target accounts to the items in the new tx df
       with <assign_targets()>:
        - checks against dbs if already:
            - known, in <cat_db>
            - unknown, in <unknowns_db>
            - fuzzy matched, in <fuzzy_db>
        - otherwise looks for a new fuzzy match
        - otherwise assigns as a new unknown
        - (function also returns the 'mode', a description of how 
           assignment was made)

    3. append any new fuzzy matches or unknowns to the corresponding db

    4. append new txs to tx_db

"""

def main(new_tx_paths, account_name, parser,
         tx_db_path    = 'tx_db.csv',
         cat_db_path   = '../persistent_cat_db.csv', 
         unknowns_path = 'unknowns_db.csv',
         fuzzy_db_path = 'fuzzy_db.csv', fuzzymatch=True):
    """Loads new transactions from input csvs in tx_db_path.

    Assigns categories by checking againts dbs for knowns,
    unknowns and previous fuzzy matches - or by carrying out
    a new fuzzy match.

    Updates dbs, including the main tx_db
    """

    # load db files to RAM
    tx_db       = pd.read_csv(tx_db_path,    index_col='date')
    cat_db      = pd.read_csv(cat_db_path,   index_col='_item')
    unknowns_db = pd.read_csv(unknowns_path, index_col='_item')
    fuzzy_db    = pd.read_csv(fuzzy_db_path, index_col='_item')

    # parse the new transactions
    new_txs = parse_new_txs(new_tx_paths, account_name, parser)

    # add categories and modes (source of categorisation)
    assignments = assign_targets(new_txs['_item'], account_name,
                                 cat_db, unknowns_db, fuzzy_db)

    new_txs = new_txs.join(pd.DataFrame(assignments, columns=['accY', 'mode']))

    # append the new unknowns to unknowns_db
    new_unknowns = new_txs.loc[new_txs['mode'] == 'new unknown',
                               ['_item', 'accY']]
    new_unknowns['accX'] = account_name

    unknowns_db = unknowns_db.append(new_unknowns[['_item', 'accX', 'accY']]
                               .set_index('_item', drop=True))
    unknowns_db.to_csv(unknowns_path)


    # append the new fuzzy matches to fuzzy_db
    new_fuzzies = new_txs.loc[new_txs['mode'] == 'new fuzzy', ['_item', 'accY']]
    new_fuzzies['status'] = 'unconfirmed'
    new_fuzzies['accX'] = account_name

    fuzzy_db = fuzzy_db.append(new_fuzzies[['_item', 'accX', 'accY', 'status']]
                               .set_index('_item', drop=True))
    fuzzy_db.to_csv(fuzzy_db_path)

    # finally append the new txs to the tx_db (with unique IDs)
    if len(tx_db>0):
        max_current = int(tx_db['id'].max())
    else: max_current = 100

    new_txs['id'] = np.arange(max_current + 1,
                              max_current + 1 + len(new_txs)).astype(int)

    new_txs['accX'] = account_name

    new_txs = (new_txs[['date', 'accX', 'accY', 'net_amt', 'ITEM', '_item',
                        'id', 'mode']].set_index('date'))

    tx_db = tx_db.append(new_txs)
    tx_db.to_csv(tx_db_path)


#------------------------------------------------------------------------------

def make_parser(input_type = 'debit_credit',
                  date_format = '%d/%m/%Y',
                  debit_sign = 'positive',
                  date = 'date',
                  ITEM = 'ITEM',
                  net_amt = 'net_amt',
                  credit_amt = 'credit_amt',
                  debit_amt = 'debit_amt'):
    """Generate a parser dict for controlling import of new txs from csv.

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

    if input_type == 'debit_credit':
        del parser['map']['net_amt']

    if input_type == 'net_amt':
        del parser['map']['credit_amt']
        del parser['map']['debit_amt']

    return parser


#------------------------------------------------------------------------------

def parse_new_txs(new_tx_paths, account_name, parser):

    """Import raw transactions from csv and return a tx_df in standard format,
    with date index, and columns: accX(from), accY(to), net_amt

    new_tx_paths : a list of csv files with new transactions
                    - will also accept a single file path

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns

    parser       : dict with instructions for processing the raw tx file

                    - 'input_type' : 'credit_debit' or 'net_amt'

                    - 'date_format': eg "%d/%m/%Y"

                    - 'map'        : dict of map for column labels
                                     (new labels are keys, old are values)

                    - 'debit_sign' : are debits shown as negative
                                     or positive numbers? (for net_amt inputs)
                                     - default is 'positive'

                 - mapping must cover following columns (i.e. new labels):

                       - net_amt: ['date', 'accX', 'accY', 'net_amt', 'ITEM']

                       - credit_debit: 'debit_amt', 'credit_amt' replace 'net_amt'


    """

    # 1. aggregate input csvs to a single df
    if not isinstance(new_tx_paths, list):
        new_tx_paths = [new_tx_paths]

    date_parser = lambda x: pd.datetime.strptime(x, parser['date_format'])

    new_tx_df = pd.concat([pd.read_csv(f, parse_dates=[parser['map']['date']],
                                          skipinitialspace=True,
                                          date_parser=date_parser,
                                          dayfirst=True)
                           for f in new_tx_paths])


    # 2. organise columns using parser, and add '_item' column
    
    new_tx_df = new_tx_df[list(parser['map'].values())]
    new_tx_df.columns = parser['map'].keys()
    new_tx_df['_item'] = new_tx_df['ITEM'].str.lower().str.strip() 

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        new_tx_df['net_amt'] = (new_tx_df['debit_amt']
                             .subtract(new_tx_df['credit_amt'], fill_value=0))

    if parser.get('debit_sign', 'positive') == 'positive':
        new_tx_df['net_amt'] *= -1
        
    return new_tx_df[['date', 'ITEM', '_item', 'net_amt']]




#------------------------------------------------------------------------------
    

def assign_targets(_items, account,
                   cat_db=None, unknowns_db=None, fuzzy_db=None,
                   fuzzymatch=True, fuzzy_threshold=75):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the 'mode' of the match) vs ref dbs (loaded in RAM)
    - returns list of tuples: (hit target, mode of assignment)

    """

    results = []
    for _item in _items:


        #    TEST                     -> TUPLE TO APPEND TO RESULTS
        # 1. is in unknowns_db?       -> ('unknown', 'old unknown')
        # 2. is in cat_db?            -> (<the hit>, 'known'      )
        # 3. is in fuzzy_db?          -> (<the hit>, 'old fuzzy'  )
        # 4. fuzzy match in tx_db?    -> (<the hit>, 'new fuzzy'  )
        # 5. ..else assign 'unknown'  -> ('unknown', 'new unknown')

        if (unknowns_db is not None and len(unknowns_db) > 0
                                   and unknowns_db.index.contains(_item)):
            results.append(('unknown', 'old unknown'))
            continue

        if cat_db is not None and cat_db.index.contains(_item):
            hits = cat_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'known'))
            continue

        if fuzzy_db is not None and fuzzy_db.index.contains(_item):
            hits = fuzzy_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'old fuzzy'))
            continue

        if fuzzymatch and cat_db is not None:
            best_match, score = process.extractOne(_item, cat_db.index.values,
                                                   scorer=fuzz.token_set_ratio)
            if score >= fuzzy_threshold:
                hits = cat_db.loc[[best_match]]
                results.append((pick_match(best_match, account, hits), 'new fuzzy'))
                continue

        results.append(('unknown', 'new unknown'))

    return results



def pick_match(item, account, hits, return_col='accY'):
    """Returns match for item in sub_df of hits, giving preference for hits
    in home account
    """
    # if only one match, return it
    if len(hits) == 1:
        return hits.loc[item,return_col]
    
    # if more than one, look for a hit in home account
    if len(hits) > 1:
        home_acc_hits = hits[hits['accX']==account]

        # if any home hits, return the first - works even if multiple
        if len(home_acc_hits) > 0:
            return home_acc_hits.iloc[0].loc[return_col]

        # if no home account hits, just return the first assigned hit
        else:
            return hits.iloc[0].loc[return_col]

