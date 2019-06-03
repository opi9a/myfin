import pandas as pd
from fuzzywuzzy import fuzz, process


def add_target_acc_col(df, acc_name, dbs):
    """
    Get target account assignments (categories)
    """
    accYs = assign_targets(df._item, acc_name,
                                unknowns_db=dbs['unknowns_db'],
                                fuzzy_db=dbs['fuzzy_db'],
                                cat_db=dbs['cat_db'])

    # make a df with accY, accY and mode columns
    df['accY'] = [x[0] for x in accYs]
    df['mode'] = [x[1] for x in accYs]

    return df


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

        if (unknowns_db is not None
              and len(unknowns_db) > 0
              and unknowns_db.index.contains(_item)):

            results.append(('unknown', 'looked up unknown'))
            continue

        if cat_db is not None and cat_db.index.contains(_item):
            hits = cat_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'looked up known'))
            continue

        if fuzzy_db is not None and fuzzy_db.index.contains(_item):
            hits = fuzzy_db.loc[[_item]]
            results.append((pick_match(_item, account, hits), 'looked up fuzzy'))
            continue

        if fuzzymatch and cat_db is not None:
            fuzzy_hit = make_fuzzy_match(_item, cat_db.index.values)

            if fuzzy_hit:
                hits = cat_db.loc[[fuzzy_hit]]
                results.append((pick_match(fuzzy_hit, account, hits),
                                'fuzzy match'))
                continue

        results.append(('unknown', 'new unknown'))

    return results


def make_fuzzy_match(input_string, reference_set, threshold=55):

    matches = {}

    scorers = { 'ratio': fuzz.ratio,
                # 'partial_ratio': fuzz.partial_ratio,
                'token_set_ratio': fuzz.token_set_ratio,
                'token_sort_ratio': fuzz.token_sort_ratio,
              }

    for scorer in scorers: 
        matches[scorer] = process.extractOne(input_string, reference_set,
                                             scorer=scorers[scorer])

    top_hit = max(matches, key=lambda x: matches[x][1])

    if matches[top_hit][1] >= threshold:
        return matches[top_hit][0]

    else:
        return False


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




