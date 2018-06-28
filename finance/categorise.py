import pandas as pd
from fuzzywuzzy import fuzz, process


def categorise(items, categ_map_path='categ_map.csv',
               new_categ_map_path=None, fuzzymatch=True, fuzzy_threshold=80):
    """Returns categories for an iterable of items, based on a lookup
    in the categ_map csv.

    Tries a fuzzy match by default.

    Assign as 'unknown' if not found, AND add item to categ_map.csv
    with 'unknown' as value.
    """
    # load the category map from csv
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


def recategorise(txdb, categ_map, return_df=False, ufunc=False):
    """Checks a tx_db against a category map and assigns categories 
    as appropriate.  Will only apply item->category maps passed, and leaves
    items not in the map untouched.

    This means can pass a partial category map (eg only those that have been
    changed) and only those will be applied.

    Accepts a dict or csv filepath as categ_map
    
    Alternative to use ufunc or iteration. As expected, ufunc
    much faster for larger sets, but may get hard to handle, so leaving
    iteration alternative

    """

    if not isinstance(categ_map, dict):
        categ_map = load_categ_map(categ_map_path)

    if ufunc:
        # this approach only works on items found in category map
        # probably preferred, as quicker and allows partial updating
        # with a new category map of any size

        # first with the 'to's
        # key step is to make a filter for 'to's in the categ map
        to_filter = txdb['item'].isin(categ_map) \
                      & (txdb['item_from_to'] == 'to')

        # then get the column with items
        to_items = txdb.loc[to_filter, 'item']

        # use them to get a list of categories from the map
        new_cats = [categ_map[x] for x in to_items]

        # finally overwrite the 'to' columns
        txdb.loc[to_filter, 'to'] = new_cats

        # now with the 'from's
        from_filter = txdb['item'].isin(categ_map) \
                        & (txdb['item_from_to'] == 'from')

        from_items = txdb.loc[from_filter, 'item']
        new_cats = [categ_map[x] for x in from_items]
        txdb.loc[from_filter, 'from'] = new_cats

    else:
    # alternative using iteration
        for ind, row in txdb.iterrows():
            from_to = row['item_from_to']
            new_cat = categ_map.get(row['item'], 'unknown')
            txdb.loc[ind,from_to] = new_cat

    if return_df: return txdb


def load_categ_map(filepath):
    """helper function to load a category map csv, returning a dict with
    all keys in lower case, stripped of leading / lagging whitespace.
    """
    categ_map = {}
    with open(filepath) as f:
        for line in f:
            a, b = line.split(',')
            categ_map[a.lower()] = b[:-1].lower().strip()

    return categ_map

