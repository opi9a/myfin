# myfin/finance/load_new_txs/load_new_txs.py

import pandas as pd
import numpy as np
from shutil import move
from pathlib import Path
import json
import subprocess

from mylogger import get_filelog

# imports from other project directories / modules
from finance.helpers.load_dbs_from_disk import load_dbs_from_disk

# imports from this directory
from .apply_parser import apply_parser
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
    logger = get_filelog(main_dir / 'log.txt')
    logger.info('*'*6 + 'calling load_new_txs() for ' + acc_path.name + '*' *6)

    dbs = load_dbs_from_disk(main_dir)

    # run any prep.py to process pre-csv input files
    if ((acc_path / 'prep.py').exists() and
         list((acc_path / 'new_pre_csvs').iterdir())):

        process_non_csv_originals(acc_path / 'new_pre_csvs')
        logger.info('processed pre_csvs')

    # get files ready for loading
    if (acc_path / 'new_csvs').exists():
        new_csv_paths = list((acc_path / 'new_csvs').iterdir())
        if new_csv_paths:
            files_to_process = new_csv_paths
            logger.info(f'found {len(new_csv_paths)} files in new_csvs')
        else:
            logger.info(f'found no new csvs to process')

    elif (acc_path / 'temp_csvs').exists():
        temp_csv_paths = list((acc_path / 'temp_csvs').iterdir())
        if temp_csv_paths:
            files_to_process = temp_csv_paths
            logger.info(f'found {len(temp_csv_paths)} files in temp_csvs')
        else:
            logger.info(f'found no new csvs to process')

    else:
        print('no new files found')
        logger.info(f'found no new csvs to process')
        return

    
    # MAIN LOOP: build df of new txs; append txs to dbs as required
    new_tx_count = 0
    for csv_file in files_to_process:
        logger.info('-'*6 + f'processing {csv_file.name}' + '-'*6)

        df = pd.read_csv(csv_file)
        logger.info(f'loaded csv with {len(df)} txs')

        if (acc_path / 'parser.json').exists():
            df = apply_parser(df, acc_path)

        df = clean_tx_df(df)

        if not 'net_amt' in df.columns:
            df['net_amt'] = (df['credit_amt']
                                 .subtract(df['debit_amt'], fill_value=0))
            logger.info(f'made net_amts')

        df['accX'] = acc_path.name
        df['_item'] = df['ITEM'].apply(lambda x: x.casefold().strip())

        df = trim_df(df, dbs['tx_db'])
        logger.info(f'after trim_df, {len(df)} txs')

        df = add_target_acc_col(df, acc_path.name, dbs)

        # TODO standardise column types etc

        dbs = append_to_all_dbs(df, dbs)
        logger.info(f'appended to dbs')

        new_tx_count += len(df)

    logger.info(f'--> Total new txs for {acc_path.name}: {new_tx_count}')

    # CLEANING UP
    if write_out_dbs:
        for db in dbs:
            dbs[db].to_csv(main_dir / (db + '.csv'))
            logger.info(f'writing out to {main_dir / (db + ".csv")}')

        archive_dbs(proj_path=main_dir, annotation='loaded_' + acc_path.name)
        logger.info(f'archived dbs')

    else:
        logger.info(f'not writing out')

    if move_new_txs:

        for file in (acc_path / 'new_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)
            logger.info(f'moved {file} to',
                        '{acc_path / "old_originals" / file.name}')

        for file in (acc_path / 'new_pre_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)

    if delete_temp_csvs and (acc_path / 'temp_csvs').exists():

        for file in (acc_path / 'temp_csvs').iterdir():
            file.unlink()

    if return_dbs:
        return(dbs)
    

