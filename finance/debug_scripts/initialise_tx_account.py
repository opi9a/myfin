# myfin/finance/debug_scripts/initialise_tx_account.py


def initialise_tx_account(acc_path):
    """Create folder structure for a new tx_account in acc_path:
        - new_pre_csvs/
            - <any new files requiring processing to make csvs>
        - processed_pre_csvs/
            - <pre_csv files after processing>
        - new_csvs/
            - <any new files>
        - processed_csvs/
            - <files after processing>
        - parser.json
        - prep.py <optional, add later>

    """

    # check making it in a tx_accounts dir
    if acc_path.parent.name != 'tx_accounts':
        print('not in a tx_accounts directory, exiting')
        return

    if acc_path.exists():
        print(acc_path, 'already exists, exiting')
        return

    acc_path.mkdir()

    # make the empty tx dirs
    for d in ['new_pre_csvs', 'processed_pre_csvs',
              'new_csvs', 'processed_csvs']:
        (acc_path / d).mkdir()

