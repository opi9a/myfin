# myfin/finance/tests/make_test_project.py

from pathlib import Path
import json
from shutil import rmtree

from .make_test_constructs import make_dbs_from_master_xlsx
from .make_test_constructs import make_acc_objects_from_master_xlsx


def make_test_project(master_xlsx_path,
                      project_dir,
                      return_dbs=True):
    """
    For an input master xlsx file, creates a project file structure, eg:

        ―
        project_dir/
        __ tx_accounts/
        ____ acc1/
        _______ new_csvs/
        _________ acc1_new_txs.csv
        _______ parser.json
        ____ acc2/
        _______ new_csvs/
        _________ acc2_new_txs.csv
        _______ parser.json
        __ tx_db.csv
        __ cat_db.csv
        __ unknowns_db.csv
        __ fuzzy_db.csv

    Optionally return the dbs in memory
    """

    project_dir = Path(project_dir)

    if project_dir.exists():
        print('removing existing project_dir', project_dir)
        rmtree(project_dir)

    project_dir.mkdir(parents=True)

    # make dict of dbs - with 'input' and 'target' elements and write to disk
    dbs = make_dbs_from_master_xlsx(master_xlsx_path)

    for db in [x for x in dbs['input'] if x.endswith('_db')]:
        path_out = project_dir / (db + '.csv')
        dbs['input'][db].to_csv(path_out, index=True)

    # make account objects (new_txs etc) and account directory structure
    accounts = make_acc_objects_from_master_xlsx(master_xlsx_path)

    for acc in accounts:
        acc_path = project_dir / 'tx_accounts' / acc
        acc_path.mkdir(parents=True)

        with (Path(acc_path) / 'parser.json').open('w') as fp:
            json.dump(accounts[acc]['parser'], fp)

        new_csvs_dir = acc_path / 'new_csvs'
        new_csvs_dir.mkdir(parents=True)

        for new_csvs_file in accounts[acc]['new_txs']:
            df = accounts[acc]['new_txs'][new_csvs_file]
            df_path = new_csvs_dir / (new_csvs_file + '.csv')
            df.to_csv(df_path, index=False)

    if return_dbs:
        return dbs

