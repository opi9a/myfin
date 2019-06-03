# myfin/debug_scripts/tidy_df.py

def tidy(df):
    """
    Drops duplicates and sorts columns

    TODO: make sort by ['date', '_item', 'accX'] (if present)
    """
    orig_index = df.index.names
    out = df.reset_index().drop_duplicates()
    out = out.sort_values(list(out.columns))
    return out.set_index(orig_index)
