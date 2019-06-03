
def check_df(df, acc_path):
    """
    TODO
    Check for balance continuity ONLY for accounts with balance.
    Pass the tx_db and take the last balance for the account.
    Use this to check for continuity across the gap, and within the
    new txs.
    """

    if balance_continuum(df).sum():
        print('WARNING:', acc_path.name, 'has a balance discontinuity')
        print(balance_continuum(df))
        return 1

    if df.duplicated().values.sum():
        print('WARNING:', acc_path.namec, 'has duplicated values')
        return 1

    return 0


