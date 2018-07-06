import pandas as pd
from fuzzywuzzy import fuzz, process

def categorise(items, txdb, account, fuzzymatch=True, fuzzy_threshold=80):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the id of the match, --> mode) vs a ref db by calling get_category()
      - ref db is really a view of passed txdb, processed as follows:
            - index by items, after applying strip() and lower()
            - columns for both accounts, id and mode
    - returns two lists, for the matched categories and the ids

    """
    # organise txdb for lookup: by item, strip() lower(),  only reqd columns
    lookup_df = (txdb.set_index(txdb['item'].str.lower(), drop=True)
                 .sort_index()[['accY','accX','id','mode']])

    # drop unknowns
    lookup_df = lookup_df.loc[lookup_df['accY'] != 'unknown']

    # get results - a list of tuples
    results = []
    for item in items:
        results.append(get_category(item, lookup_df, account,
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



