# myfin/finance/debug_scripts/initialise_tx_account.py

from pathlib import Path

def initialise_tx_account(project_path, account_name):
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

    acc_path = Path(project_path).expanduser() / 'tx_accounts' / account_name

    if acc_path.exists():
        print(acc_path, 'already exists, exiting')
        return

    print(f'making account dir at {acc_path}')
    acc_path.mkdir()

    # make the empty tx dirs
    for d in ['new_pre_csvs', 'temp_csvs', 'new_csvs', 'old_originals']:
        (acc_path / d).mkdir()

