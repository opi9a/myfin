import pandas as pd

def append_to_all_dbs(df, dbs):
    """
    Appends reqd rows to dbs, based on passed new txs df.
    """
    dbs['fuzzy_db']    = append_to_fuzzy_db(df, dbs['fuzzy_db'])
    dbs['unknowns_db'] = append_to_unknowns_db(df, dbs['unknowns_db'])
    dbs['tx_db']       = append_to_tx_db(df, dbs['tx_db'])

    return dbs

def append_to_fuzzy_db(df, fuzzy_db):
    """
    Get any fuzzy matches and append to fuzzy_db
    """

    new_fuzzies = (df.loc[df['mode'] == 'fuzzy match']
                     .set_index('_item', drop=True))
    new_fuzzies['status'] = 'unconfirmed'
    new_fuzzies = new_fuzzies[fuzzy_db.columns]

    return tidy(fuzzy_db.append(new_fuzzies))


def append_to_unknowns_db(df, unknowns_db):
    """
    Get any new unknowns and append to unknowns_db
    """
    new_unknowns = (df.loc[df['mode'] == 'new unknown']
                     .set_index('_item', drop=True))
    unknowns_db = unknowns_db.append(new_unknowns[unknowns_db.columns])

    return tidy(unknowns_db)


def append_to_tx_db(df, tx_db):
    """
    Assign ids to the new txs and append to tx_db
    """
    if len(tx_db):
        max_current = tx_db['id'].max()
    else:
        max_current = 100

    df['id'] = pd.np.arange(max_current + 1,
                         max_current + 1 + len(df)).astype(int)

    df_out = tx_db.append(df[tx_db.columns])
    df_out.index.name = 'date'

    return df_out


def tidy(df):
    orig_index = df.index.names
    out = df.reset_index().drop_duplicates()
    out = out.sort_values(list(out.columns))
    return out.set_index(orig_index)


