# myfin/finance/load_new_txs/archive_dbs.py

from pathlib import Path
import pandas as pd
from shutil import copy

from finance.helpers.constants import DB_NAMES

def archive_dbs(proj_path=None, annotation=None, archive_path=None):
    """
    Save a snapshot of the 4 dbs
    """

    if proj_path is None:
        proj_path = Path()

    proj_name = proj_path.name

    if archive_path is None:
        archive_path = proj_path / 'db_archive'

    if not Path(archive_path).exists():
        Path(archive_path).mkdir()

    ts = pd.datetime.now().strftime("%Y%m%d_%H%M")


    if annotation is None:
        annotation = ""
    else:
        annotation = "_" + annotation

    for db in DB_NAMES:

        dir_out = archive_path / db
        if not Path(dir_out).exists():
            Path(dir_out).mkdir()

        copy(str(proj_path / (db + '.csv')), 
             str(dir_out / (ts + annotation + '.csv') ))

