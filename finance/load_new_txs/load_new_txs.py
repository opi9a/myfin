# myfin/finance/load_new_txs/load_new_txs.py

import pandas as pd
import numpy as np
from shutil import move, copy
from pathlib import Path
import json
import subprocess

from mylogger import get_filelog

# imports from other project directories / modules
from finance.helpers.load_dbs_from_disk import load_dbs_from_disk

# imports from this directory
from .load_new_csv_files import load_new_csv_files
from .trim_df import trim_df
from .clean_tx_df import clean_tx_df
from .add_target_acc_col import add_target_acc_col
from .append_to_dbs import append_to_all_dbs
from .archive_dbs import archive_dbs


def load_new_txs(acc_path, 
                 return_dbs=False, write_out_dbs=True,
                 move_new_txs=True, delete_temp_csvs=True):

    """
    Function to load new transactions from input files for an account
    at acc_path.  Called for each account.

    Account file structure:
        - new_csvs (original csv files not needing pre-processing)
        - new_pre_csvs (originals needing processing to csvs, eg pdfs)
        - temp_csvs (csvs made by processing new_pre_csvs)
        - old_originals (new_csvs or new_pre_csvs after loading)
    """

    # PREPARATION 
    acc_path = Path(acc_path).absolute()

    if not 'tx_accounts' in str(acc_path):
        print(f'no "tx_accounts" found in {acc_path} - does not look like a path')
        return

    main_dir = acc_path.parents[1]
    parser = None

    dbs = load_dbs_from_disk(main_dir)

    # run any prep.py to process pre-csv input files
    if ((acc_path / 'prep.py').exists() and
         list((acc_path / 'new_pre_csvs').iterdir())):

        process_non_csv_originals(acc_path / 'new_pre_csvs')

    # get path to files ready for loading
    if list((acc_path / 'new_csvs').iterdir()):
        files_to_process_path = acc_path / 'new_csvs'

    elif list((acc_path / 'temp_csvs').iterdir()):
        files_to_process_path = acc_path / 'temp_csvs'

    else:
        print('no new files found')
        return

    
    # MAIN LOOP: build df of new txs; append txs to dbs as required
    for csv_file in files_to_process_path.iterdir():

        df = pd.read_csv(csv_file)

        if (acc_path / 'parser.json').exists():
            parser = json.load((acc_path / 'parser.json').open())
            df = df[list(parser['map'].values())]
            df.columns = parser['map'].keys()
            df['source'] = acc_path.name

            if ('net_amt' in df.columns and
                parser.get('debit_sign', 'negative') == 'positive'):
                df['net_amt'] *= -1

        df = clean_tx_df(df)

        if not 'net_amt' in df.columns:
            df['net_amt'] = (df['credit_amt']
                                 .subtract(df['debit_amt'], fill_value=0))

        df['accX'] = acc_path.name
        df['_item'] = df['ITEM'].apply(lambda x: x.casefold().strip())

        df = trim_df(df, dbs['tx_db'])
        df = add_target_acc_col(df, acc_path.name, dbs)

        # TODO standardise column types etc

        dbs = append_to_all_dbs(df, dbs)


    # CLEANING UP
    if write_out_dbs:
        for db in dbs:
            dbs[db].to_csv(main_dir / (db + '.csv'))

        archive_dbs(proj_path=main_dir, annotation='loaded_' + acc_path.name)

    if move_new_txs:

        for file in (acc_path / 'new_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)

        for file in (acc_path / 'new_pre_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)

    if delete_temp_csvs and (acc_path / 'temp_csvs').exists():

        for file in (acc_path / 'temp_csvs').iterdir():
            file.unlink()

    if return_dbs:
        return(dbs)
    

