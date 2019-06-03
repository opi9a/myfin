# myfin/finance/load_new_txs/load_new_txs.py

import pandas as pd
import numpy as np
from shutil import move, copy
from pathlib import Path
import json
import subprocess

from mylogger import get_filelog

# imports from other project directories / modules
from finance.helpers.constants import DB_NAMES
from finance.helpers.get_dirs import get_dirs
from finance.helpers.load_dbs_from_disk import load_dbs_from_disk

# imports from this directory
from .trim_df import trim_df
from .load_new_csv_files import load_new_csv_files
from .add_target_acc_col import add_target_acc_col
from .append_to_dbs import append_to_all_dbs


"""
Sequence:

Begin with new raw input files in <acc_path> / new_originals.

PREPARING CSVS

Generates files in prepared_csvs/ with correct basic columns:
    - 'date', 'ITEM'
    - either: 'net_amt', or 'credit_amt', 'debit_amt' depending on type
    - 'source'

If there is a prep.py, then execute it:
    - will generate csv files with basic cols and put in prepared_csvs/
    - NB must have basic cols in 'net_amt' format

Else if there is a parser.json, then call assign_base_cols for each
file in new_originals.

Else just copy the files from new_originals/ to prepared_csvs/


LOADING AND CONCATENATING CSVS

Uses pd.read_csv() and pd.concat() to generate a df of new_txs from
the files in prepared_csvs/.
    

FORMATTING NEW_TXS DF

Assign derived columns to the new_txs df:
    - 'net_amt' if was 'credit_debit' type (requires parser)
    - formatted date
    - standardised '_item'


TRIMMING OVERLAP

Drop any transactions already loaded into tx_db.
Assign 'id' to be consistent with tx_db transactions.


ASSIGNING TARGET ACCOUNT

Adds a columns with 'accY', the target account, aka category
(eg 'groceries', 'Midland Bank Savings Acc').

Works by trying lookups in cat_db, fuzzy_db, unknowns_db, then
trying a fuzzy match, and assigning 'unknown' if fails.  

Also adds a column with the 'mode' by which 'accY' was assigned:
    - 'looked up known', 'looked up fuzzy', 'looked up unknown'
      'fuzzy match', 'new unknown'


APPENDING TO DBS

Append new_txs to tx_db and write out.
Append relevant new entries to fuzzy_db, unknowns_db and write out.
(NB cat_db cannot require any updates, as new 'knowns' can only be
assigned manually)


CLEARING UP

Move processed files from new_originals/ to old_originals/
"""


def load_new(acc_name, main_dir,
             return_dbs=False, write_out_dbs=True, move_new_txs=True):
    """
    Main function for loading new txs for an account, processing them,
    adding to dbs ('tx_db', 'unknowns_db', fuzzy_db') and writing to disk.
    """

    main_dir = Path(main_dir).absolute()
    acc_path = main_dir / 'tx_accounts' / acc_name

    dbs = load_dbs_from_disk(main_dir)

    prepare_new_csv_files(acc_path.absolute())

    new_csv_files = get_dirs(acc_path)['new_csvs']

    if not new_csv_files:
        print('no new csvs in account', acc_name)
        return

    df = load_new_csv_files(acc_path)
    df = trim_df(df, dbs['tx_db'], acc_name)
    df['accX'] = acc_path.name
    df = add_target_acc_col(df, acc_path, dbs)

    # check for discontinuity only if account reports balance
    # df_check = check_df(df, acc_path)

    dbs = append_to_all_dbs(df, dbs)

    if move_new_txs:
        for f in new_csv_files:
            move(f, acc_path / 'processed_csvs' / f.name)

    if write_out_dbs:
        for db in dbs:
            dbs[db].to_csv(main_dir / (db + '.csv'))

        archive_dbs(proj_path=main_dir, annotation='loaded_' + acc_name)

    if return_dbs:
        return(dbs)


def prepare_new_csv_files(dir_path):
    """
    Execute script to generate prepared csvs by calling python through host os
    using subprocess.run().
    """
    prep_script_path = dir_path.absolute() / 'prep.py'
    if prep_script_path.exists():
        subprocess.run(['python', str(prep_script_path.absolute()),
                        str(dir_path)])
    else:
        pass


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

