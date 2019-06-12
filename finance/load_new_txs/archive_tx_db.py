# myfin/finance/load_new_txs/archive_tx_db.py

from pathlib import Path
from shutil import copy
import pandas as pd


def archive_tx_db(proj_path=None, annotation=None, archive_path=None):
    """
    Save a snapshot of the 4 dbs
    """

    if proj_path is None:
        proj_path = Path()

    if archive_path is None:
        archive_path = proj_path / 'db_archive'

    if not Path(archive_path).exists():
        Path(archive_path).mkdir()

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M")


    if annotation is None:
        annotation = ""
    else:
        annotation = "_" + annotation

    dir_out = archive_path / 'tx_db.csv'
    if not Path(dir_out).exists():
        Path(dir_out).mkdir()

    copy(str(proj_path / 'tx_db.csv'),
         str(dir_out / (ts + annotation + '.csv')))
