import pandas as pd
from fuzzywuzzy import fuzz, process

    
def categorise(items, account, txdb=None, cat_db=None, fuzzymatch=True, fuzzy_threshold=80):
    """
    - take iterable of items - eg column of new_tx df
    - iterate over items (df.apply is not faster), generating matches
      (and the id of the match, --> mode) vs a ref db by calling get_category()
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
    
    itemised = txdb.set_index(txdb['item'].str.lower(), drop=False)

    if drop_unknowns:
        itemised = itemised.loc[itemised['accY'] != 'unknown'].drop('item', axis=1)

    return itemised


def pick_match(item, account, sub_df):
    """Returns match for item in sub_df of matches, giving preference for hits
    in home account
    """
    # if only one match, return it
    if len(sub_df) == 1:
        return (sub_df.loc[item,'accY'],
                sub_df.loc[item,'id'])
    
    # if more than one, look for a hit in home account
    if len(sub_df) > 1:
        home_acc_hits = sub_df[sub_df['accX']==account]

        # if any home hits, return the first - works even if multiple
        if len(home_acc_hits) > 0:
            return (home_acc_hits.iloc[0].loc['accY'], 
                    home_acc_hits.iloc[0].loc['id'])

        # if no home account hits, just return the first assigned hit
        else:
            return (sub_df.iloc[0].loc['accY'], 
                    sub_df.iloc[0].loc['id'])


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

    return tx_by_item

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


def recategorise(txdb_path):
    # load txdb, and select unknowns
    txdb = pd.read_csv(txdb_path, index_col='date')
    
    # from that, get a list of items
    items = txdb.loc[txdb['accY']=='unknown', 'item']
    
    # use items to return hits and modes for the unknowns
    hits, modes = categorise(items, txdb, 'halifax_cc')
    
    # over-write the txdb - modes first, as after hits they aren't 'unknown'
    txdb.loc[txdb['accY']=='unknown', 'mode'] = modes
    txdb.loc[txdb['accY']=='unknown', 'accY'] = hits
    
    # write out
    txdb.to_csv('txdb.csv')
