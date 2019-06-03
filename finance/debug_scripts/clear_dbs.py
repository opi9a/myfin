# myfin/debug_scripts/clear_dbs.py

import pandas as pd

def clear_dbs(acc_path=Path()):
    """
    Clears dbs except cat_db
    """

    acc_path = Path(acc_path)

    for db in DB_NAMES:
        if db != 'cat_db':
            db_path = acc_path / (db + '.csv')
            df = pd.read_csv(db_path, index_col=None).iloc[0:0,:]
            print(db, df)
            df.to_csv(db_path, index=False)


