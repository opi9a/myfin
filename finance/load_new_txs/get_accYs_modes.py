# myfin/finance/load_new_txs/get_accYs_modes.py

import pandas as pd

from finance.load_new_txs.make_fuzzy_match import make_fuzzy_match


def get_accYs_modes(_items, account_name, tx_db, cat_db=None):
    """
    Assigns 'acc_y' and 'mode' columns to input df, based on passed tx_db
    and optional external cat_db.

    Looks for hits from direct lookup of '_item', or lookup of a fuzzy
    match for item, in a ref_db (tx_db + cat_db).  The best match picked
    from those using prioritisation criteria (eg if is in same accX, if
    was confirmed etc).

    TODO: use prioritisation criteria in choice of fuzzy match?  (Or integrate
          fuzzy matching with choosing a hit, eg choosing based on fuzzy score
          as well as prioritisation criteria).

    """
    # TODO: subset tx_db (rows / cols?)

    lookup_cols = ['accX', 'accY', 'mode']

    tx_db = tx_db.reset_index().set_index('_item')[lookup_cols]

    if cat_db is not None:
        cat_db['mode'] = 'cat_db'

    ref_db = tx_db if cat_db is None else pd.concat([tx_db, cat_db])

    acc_ys = []
    modes = []

    for _item in _items:

        match_type = None
        hits = None

        # try direct look up
        if _item in ref_db.index:
            hits = ref_db.loc[[_item]]
            match_type = 'direct'

        # try looking up a fuzzy-matched item (if can get one)
        else:
            fuzzy_matched_item = make_fuzzy_match(_item, ref_db.index)

            if fuzzy_matched_item is not None:
                hits = ref_db.loc[[fuzzy_matched_item]]
                match_type = 'fuzzy'

        if match_type is None:
            acc_ys.append('unknown')
            modes.append('not_matched')

        elif match_type == 'direct':
            acc_y, mode = pick_hit(hits, account_name)
            acc_ys.append(acc_y)
            modes.append(mode)

        elif match_type == 'fuzzy':
            acc_y, _ = pick_hit(hits, account_name)
            acc_ys.append(acc_y)
            modes.append('fuzzy')

    return acc_ys, modes


def pick_hit(hits, accX_name):
    """
    Returns match, mode tuple for _item in sub_df of hits,
    giving preference for hits in home account
    """
    # if only one match, return it
    if len(hits) == 1:
        return tuple(hits.iloc[0].loc[['accY', 'mode']])

    # if more than one, look for a hit in home account
    home_acc_hits = hits[hits['accX'] == accX_name]

    # if any home hits, return the first
    if not home_acc_hits.empty:
        return tuple(home_acc_hits.iloc[0].loc[['accY', 'mode']])

    # if no home account hits, just return the first assigned hit
    return tuple(hits.iloc[0].loc[['accY', 'mode']])
