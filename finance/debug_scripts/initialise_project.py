# myfin/finance/debug_scripts/initialise_project.py

import pandas as pd

from pathlib import Path
from shutil import rmtree, copy

from finance.helpers.constants import TX_DB_COLUMNS

"""
Perhaps obsolete but should still work and may still be useful.

Will need to sort imports
"""

def initialise_project(proj_name, overwrite_existing=False,
                       parent_dir=None,
                       dbs_to_import=None,
                      ):

    """Required structure:

        proj_name/
        --- tx_db.csv
        --- cat_db.csv
        --- unknowns_db.csv
        --- fuzzy_db.csv
        --- log.txt
        --- tx_accounts/
        
        The csv files to contain column headings and index as appropriate, 
        but no rows.
    """


    # start from wherever called and make a directory with proj_name
    if parent_dir is None:
        parent_dir = Path().expanduser()

    proj_path = Path(parent_dir) / proj_name

    print('\ninitialising project at:', proj_path)

    if not proj_path.exists():
        print('trying to create', proj_path)
        proj_path.mkdir()

    elif overwrite_existing:
        print(proj_name, 'exists already, overwriting it')
        rmtree(proj_path)
        proj_path.mkdir()

    else:
        print("A project with that name already exists in this directory.\
              pass 'overwrite_existing=True' to overwrite it")
        return 1

    # handy set of columns 

    # tx_db
    ind = pd.DatetimeIndex(start='1/1/1970', periods=0, freq='D', name='date')
    df = pd.DataFrame(columns=TX_DB_COLUMNS, index=ind)
    df.to_csv((proj_path / 'tx_db.csv'), index=True)

    # work out what dbs to import
    base_db_columns=['_item', 'accX', 'accY']
    for db in ['cat_db', 'unknowns_db', 'fuzzy_db']:

        db_to_load = [x for x in dbs_to_import if db in str(x)]

        if len(db_to_load) > 1:
            print(f'too many dbs named {db} in {dbs_to_import}')
            return 1

        if len(db_to_load) == 1:
            print('found db to load:', db_to_load)
            copy(db_to_load[0], (proj_path / (db + '.csv')))

        else:
            print('making empty', db)
            cols_to_use = base_db_columns
            if db == 'fuzzy_db':
                cols_to_use = base_db_columns + ['status']
            pd.DataFrame(columns=cols_to_use).to_csv((proj_path / (db + '.csv')),
                                                index=False)

    # make tx_accounts dir
    (proj_path / 'tx_accounts').mkdir()

    return proj_name


