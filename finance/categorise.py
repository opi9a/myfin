import pandas as pd
from fuzzywuzzy import fuzz, process

    
def categorise(ITEMs, account, tx_db=None, cat_db=None, unknowns_db=None, fuzzy_db=None,
               fuzzymatch=True, fuzzy_threshold=80):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the id of the match, --> mode) vs a ref db
      - ref db is really a view of passed tx_db, processed as follows:
            - index by items, after applying strip() and lower()
            - columns for both accounts, id and mode
    - returns two lists, for the matched categories and the ids

    """

    # print('unknowns_db', unknowns_db, end='\n\n')
    # print('cat_db', cat_db, end='\n\n')
    # print('tx_db', tx_db, end='\n\n')
    # print('fuzzy_db', fuzzy_db, end='\n\n')


    # get results - a list of tuples
    results = []
    for ITEM in ITEMs:
        # print("\nnow with item:", ITEM)

        _item = ITEM.lower().strip()

        # 1. check in unknowns_db   -> append ('unknown', -1) <old unknown>
        # 2. check in cat_db        -> append (<hit>,      1) <known>
        # 3. check in fuzzy_db      -> append (<hit>,      2) <old fuzzy>
        # 4. fuzzy match on tx_db   -> append (<hit>,      3) <new fuzzy>
        # 5. just assign 'unknown'  -> append ('unknown',  0) <new unknown>

        # pass dbs to this function in RAM for lookups
        # return assignments and modes tuples (in a list)
        # don't append to dbs - do all at once later in load_new_tx(),
        # based on the modes assigned to the new_txs

        # 1. check in unknowns_db   -> append ('unknown', -1) <old unknown>
        if (unknowns_db is not None and len(unknowns_db) > 0
                                   and unknowns_db.index.contains(_item)):
            # print('unknown\n')
            results.append(('unknown', -1))
            # print(results[-1])
            continue

        # 2. check in cat_db        -> append (<hit>,      1) <known>
        if cat_db is not None and cat_db.index.contains(_item):
            # print('a known hit')
            hits = cat_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 1))
            # print(results[-1])
            continue

        # 3. check in fuzzy_db      -> append (<hit>,      2) <old fuzzy>
        if fuzzy_db is not None and fuzzy_db.index.contains(ITEM):
            # print('a fuzzy hit')
            hits = fuzzy_db.loc[[ITEM]]
            results.append((pick_match(_item, account, hits, return_col='match_accY'), 2))
            # print(results[-1])
            continue

        # 4. fuzzy match on tx_db   -> append (<hit>,      3) <new fuzzy>
        if fuzzymatch and len(tx_db>0):
            # print('trying a fuzzy match')
            best_match, score = process.extractOne(ITEM, tx_db['ITEM'].values,
                                                   scorer=fuzz.token_set_ratio)
            # print(best_match, score)
            if score >= fuzzy_threshold:
                # get a subdf of the best match
                hits = tx_db.loc[tx_db['ITEM']==best_match].set_index('ITEM')
                res = pick_match(best_match, account, hits)
                results.append((res, 3))
                new_match_accX = hits.loc[best_match, 'accX']
                new_match_id = hits.loc[best_match, 'id']
                fuzzy_db.loc[ITEM] = [account, best_match,
                                      new_match_accX, res, new_match_id, 'unconfirmed'] 
                # print(results[-1])
                continue

        # 5. just assign 'unknown'  -> append ('unknown',  0) <new unknown>
        results.append(('unknown', 0))

    # return [x[0] for x in results], [x[1] for x in results] 
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

