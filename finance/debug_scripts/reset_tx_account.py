# myfin/finance/debug_scripts/reset_tx_account.py

def reset_tx_account(tx_account_path=None):
    """
    Restore a tx_account to unprocessed state, retaining original input
    data.

    If there are processed_pre_csvs, move these to new_pre_csvs and
    delete everything else.

    Otherwise move processed_csvs to new_csvs.
    """

    if tx_account_path is None:
        tx_account_path = Path('.')
    else:
        tx_account_path = Path(tx_account_path)

    print('\nResetting', tx_account_path.absolute().name)

    dirs = get_dirs(tx_account_path)

    print('\nStructure before reset')
    for dir in dirs:
        print(("- " + dir).ljust(20), str(len(dirs[dir])).rjust(3))

    if dirs.get('processed_pre_csvs', False):
        print('\nfound processed_pre_csvs so move to new_pre_csvs '
              'and delete everything else')
        for f in dirs['processed_pre_csvs']:
            f.rename(tx_account_path / 'new_pre_csvs' / f.name)
        
        clean_dir(tx_account_path / 'new_csvs', False)
        clean_dir(tx_account_path / 'processed_csvs', False)

    if dirs.get('processed_csvs', False):
        print('\nfound processed_csvs so move to new_csvs')
        for f in dirs['processed_csvs']:
            f.rename(tx_account_path / 'new_csvs' / f.name)
        
    print('\nStructure after reset')
    dirs = get_dirs(tx_account_path)

    for dir in dirs:
        print(("- " + dir).ljust(20), str(len(dirs[dir])).rjust(3))


