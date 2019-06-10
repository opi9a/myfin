# finance.helpers.load_dbs_from_disk.py

from pathlib import Path
import pandas as pd


def load_dbs_from_disk(dir_path=Path()):
    """
    Loads dbs from disk, returning a dict
    """

    dir_path = Path(dir_path)

    dbs = {}

    for db in ['tx_db', 'cat_db']:
        dbs[db] = pd.read_csv(dir_path / (db + '.csv'),
                              index_col='date' if db == 'tx_db' else '_item')

    dbs['tx_db'].index = pd.to_datetime(dbs['tx_db'].index)

    return dbs



