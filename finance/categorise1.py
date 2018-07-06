import pandas as pd
from fuzzywuzzy import fuzz, process

"""

categorise():
    - takes iterable of items
    - looks each up in categ_map
    - three results:
        - match known -> return the category, and the id of match
        - match 'unknown' -> return the category, and the id of match
        - fuzzy match -> return the category, and id of best_match
        - no match -> return 'unknown'

"""
def categorise1(items, txdb, account, fuzzymatch=True, fuzzy_threshold=80):
    """
    - take items column of new_tx df
    - use df.apply with get_category, and the txdb to generate categories
        - need to process the txdb: 
            - index by items, after applying strip() and lower()
            - columns for both accounts, id and mode

        - eg from notebook
            by_item = (df.set_index(df['item'].str.lower(), drop=True)
               .sort_index()[['accY','accX','id','mode']])

    """
    # organise txdb for lookup: by item, strip() lower(),  only reqd columns
    items_df = (txdb.set_index(txdb['item'].str.lower(), drop=True)
               .sort_index()[['accY','accX','id','mode']])

    # drop unknowns
    items_df = items_df.loc[items_df['accY'] != 'unknown']

    # get results - a list of tuples
    results = []
    for item in items:
        results.append(get_category(item, items_df, account,
                                    fuzzymatch, fuzzy_threshold))

    return [x[0] for x in results], [x[1] for x in results] 



def get_category(item, tx_by_item, account=None, fuzzymatch=True, fuzzy_threshold=80):
    """Looks up category for a single item in a tx df that has been organised
    by item (lower case and stripped). Also should get rid of unknows first
    (effient to do before repeatedly calling this function on the df).

    Returns a tuple of the lookup value and the id of the tx used to assign it

    Logic is
        - are there any assigned hits with mode=-1
            - if one of these, return it
            - if more than one
                - if one matches account, return it
                - if not, return random (but not 'unknown')
        - else are there unassigned hits, with mode >-1
            - repeat as above
        - else fuzzy match using whole txdb
        - else return 'unknown'
    """

    # first drop anything where assigned category is 'unknown'
    # - better done in preparing the input argument to this func, 
    # which will be used many times
    tx_by_item = tx_by_item.loc[tx_by_item['accY'] != 'unknown']

    if tx_by_item.index.contains(item):
        item_df = tx_by_item.loc[[item],:]

        # make a sub_df of hits manually assigned (i.e. with mode -1)
        assigned_hits = item_df.loc[item_df['mode'] == -1]

        # if only one, return it
        if len(assigned_hits) == 1:
            return (assigned_hits.loc[item,'accY'],
                    assigned_hits.loc[item,'id'])
        
        # if more than one, look for a hit in home account
        if len(assigned_hits) > 1:
            home_acc_hits = assigned_hits[assigned_hits['accX']==account]

            # return the first - works even if multiple
            if len(home_acc_hits) > 0:
                return (home_acc_hits.iloc[0].loc['accY'], 
                        home_acc_hits.iloc[0].loc['id'])

            # if no home account hits, just return the first assigned hit
            else:
                return (assigned_hits.iloc[0].loc['accY'], 
                        assigned_hits.iloc[0].loc['id'])



        # if pasting from above, remember to change mode (from -1)
        # as well as assigned-->unassigned

        # make a sub_df of hits not manually assigned (i.e. mode > -1)
        unassigned_hits = item_df.loc[item_df['mode'] > -1]

        if len(unassigned_hits) == 1:
            return (unassigned_hits.loc[item,'accY'],
                    unassigned_hits.loc[item,'id'])
        
        if len(unassigned_hits) > 1:
            home_acc_hits = unassigned_hits[unassigned_hits['accX']==account]

            if len(home_acc_hits) > 0:
                return (home_acc_hits.iloc[0].loc['accY'], 
                        home_acc_hits.iloc[0].loc['id'])

            # if no home account hits, just return the first unassigned hit
            else:
                return (unassigned_hits.iloc[0].loc['accY'], 
                        unassigned_hits.iloc[0].loc['id'])

    # for fuzzy matching, test against whole index
    if fuzzymatch:
        best_match, score = process.extractOne(item, tx_by_item.index,
                                               scorer=fuzz.token_set_ratio)

        # just return the first - so works if single or multiple
        if score >= fuzzy_threshold:
            return (tx_by_item.loc[[best_match],'accY'].iloc[0],
                    tx_by_item.loc[[best_match],'id'].iloc[0])

    # if nothing's returned by now, there's no match
    return 'unknown', 0



def categorise(items, txdb, fuzzymatch=True, fuzzy_threshold=80):
    """Returns categories for an iterable of items, based on a lookup
    in the tx database

    Tries a fuzzy match by default.

    Assign as 'unknown' if not found, AND add item to categ_map.csv
    with 'unknown' as value.
    """
    categ_map = load_categ_map(categ_map_path)

    # list to hold the categories to return, corresponding to items
    categories = []

    # new assignments to append to categ_map
    new_assigns = {'new_item':[], 'new_category':[]}

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
                # with open('logs/log.txt', 'a') as f:
                #     print(f'Fuzzy-matched {item}, with {best_match}, scoring {score}', file=f)

            else:
                categories.append('unknown')
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append('unknown')
                # with open('log.txt', 'a') as f:
                #     print(f'No fuzzy match for {item} (best score {score})', file=f)

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


def recategorise(txdb, categ_map, excl_unknowns=False,
                        return_df=False, ufunc=False):
    """Checks a tx_db against a category map and assigns categories 
    as appropriate.  Will only apply item->category maps passed, and leaves
    items not in the map untouched.

    This means can pass a partial category map (eg only those that have been
    changed) and only those will be applied.

    Accepts a dict or csv filepath as categ_map

    excl_unknowns means 
    
    Alternative to use ufunc or iteration. As expected, ufunc
    much faster for larger sets, but may get hard to handle, so leaving
    iteration alternative

    TODO: check all the lower() and strip() below is reqd
    """

    if not isinstance(categ_map, dict):
        categ_map = load_categ_map(categ_map)

    if excl_unknowns:
        categ_map = {k:v for k,v in categ_map.items() if v != 'unknown'}

    if ufunc:
        # this approach only works on items found in category map
        # probably preferred, as quicker and allows partial updating
        # with a new category map of any size

        # first with the 'to's
        # key step is to make a filter for 'to's in the categ map
        # - could do this with apply, for fuzzy match?
        to_filter = txdb['item'].str.strip().str.lower().isin(categ_map) \
                      & (txdb['item_from_to'] == 'to')

        # then get the column with items
        to_items = txdb.loc[to_filter, 'item']

        # use them to get a list of categories from the map
        new_cats = [categ_map[x.lower().strip()] for x in to_items]

        # finally overwrite the 'to' columns
        txdb.loc[to_filter, 'to'] = new_cats

        # now with the 'from's
        from_filter = txdb['item'].str.strip().str.lower().isin(categ_map) \
                        & (txdb['item_from_to'] == 'from')

        from_items = txdb.loc[from_filter, 'item']
        new_cats = [categ_map[x.lower().strip()] for x in from_items]
        txdb.loc[from_filter, 'from'] = new_cats

    else:
    # alternative using iteration
        for ind, row in txdb.iterrows():
            from_to = row['item_from_to']
            new_cat = categ_map.get(row['item'], 'unknown')
            txdb.loc[ind,from_to] = new_cat

    if return_df: return txdb


def load_categ_map(filepath, ignore_header=True):
    """helper function to load a category map csv, returning a dict with
    all keys in lower case, stripped of leading / lagging whitespace.
    """
    categ_map = {}
    with open(filepath) as f:
        if ignore_header:
            f.readline()
        for line in f:
            a, b = line.split(',')
            categ_map[a.lower()] = b[:-1].lower().strip()

    return categ_map

