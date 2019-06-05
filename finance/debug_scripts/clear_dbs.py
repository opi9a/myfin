# myfin/debug_scripts/clear_dbs.py

from pathlib import Path
import pandas as pd

from finance.helpers.constants import DB_NAMES

def clear_dbs(project_path):
    """
    Clears dbs except cat_db
    """

    project_path = Path(project_path)

    for db in DB_NAMES:
        if db != 'cat_db':
            db_path = project_path / (db + '.csv')
            df = pd.read_csv(db_path, index_col=None).iloc[0:0,:]
            print(db, df)
            df.to_csv(db_path, index=False)


