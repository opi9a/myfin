# myfin/finance/update_dbs/write_out_dbs.py

from pathlib import Path
from finance.load_new_txs import archive_dbs

def write_out_dbs(dbs, acc_path, archive=True, annotation=None):
    """
    Helper function to write out the dbs in passed dict to appropriate
    files in acc_path.

    Optionally archive them with the passed annotation
    """

    acc_path = Path(acc_path)

    for db in dbs:
        dbs[db].to_csv(acc_path / (db + '.csv'))

    if archive:
        archive_dbs(acc_path=acc_path, annotation=annotation)


