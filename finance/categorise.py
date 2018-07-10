import pandas as pd
from fuzzywuzzy import fuzz, process

    
def categorise(items, account, txdb=None, cat_db=None, fuzzymatch=True, fuzzy_threshold=80):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the id of the match, --> mode) vs a ref db
      - ref db is really a view of passed txdb, processed as follows:
            - index by items, after applying strip() and lower()
            - columns for both accounts, id and mode
    - returns two lists, for the matched categories and the ids

    """
    if txdb is None and cat_db is None:
        print("need a txdb and/or a cat_db")
        return 1

    # organise txdb for lookup by item (lower, stripped, no 'unknown's)
    txdb_by_item = itemise(txdb)[['accY','accX','id','mode']]

    # get results - a list of tuples
    results = []
    for item in items:

        item = item.lower().strip()

        if txdb_by_item.index.contains(item):
            item_subdf = txdb_by_item.loc[[item],:]

            # 1. try assigned hits in txdb
            assigned_hits = item_subdf.loc[item_subdf['mode'] == -1]
            if len(assigned_hits) > 0:
                results.append(pick_match(item, account, assigned_hits))
                continue

            # 2. try unassigned hits in txdb
            unassigned_hits = item_subdf.loc[item_subdf['mode'] > -1]
            if len(unassigned_hits) > 0:
                results.append(pick_match(item, account, unassigned_hits))
                continue

        # 3. try fuzzy match - test against whole index
        if fuzzymatch:
            best_match, score = process.extractOne(item, txdb_by_item.index,
                                                   scorer=fuzz.token_set_ratio)

            # just return the first - so works if single or multiple
            if score >= fuzzy_threshold:
                results.append((txdb_by_item.loc[[best_match],'accY'].iloc[0],
                                txdb_by_item.loc[[best_match],'id'].iloc[0]))
                continue

        # 4. if nothing's returned by now, there's no match
        results.append(('unknown', 0))

    # return [x[0] for x in results], [x[1] for x in results] 
    return results


def itemise(txdb, drop_unknowns=True):
    """Reorganises a tx dataframe to support querying for category by item:
        - apply strip() and lower() to 'item' field
        - set 'item' as index

    Returns all columns (doesn't apply a selection, eg for just
                         'accY', 'accX', 'id', 'mode')
    """
    
    itemised = txdb.set_index(txdb['item'].str.lower().str.strip(), drop=False)

    if drop_unknowns:
        itemised = itemised.loc[itemised['accY'] != 'unknown'].drop('item',
                                                                        axis=1)
    return itemised


def pick_match(item, account, matches):
    """Returns match for item in sub_df of matches, giving preference for hits
    in home account
    """
    # if only one match, return it
    if len(matches) == 1:
        return (matches.loc[item,'accY'],
                matches.loc[item,'id'])
    
    # if more than one, look for a hit in home account
    if len(matches) > 1:
        home_acc_hits = matches[matches['accX']==account]

        # if any home hits, return the first - works even if multiple
        if len(home_acc_hits) > 0:
            return (home_acc_hits.iloc[0].loc['accY'], 
                    home_acc_hits.iloc[0].loc['id'])

        # if no home account hits, just return the first assigned hit
        else:
            return (matches.iloc[0].loc['accY'], 
                    matches.iloc[0].loc['id'])

