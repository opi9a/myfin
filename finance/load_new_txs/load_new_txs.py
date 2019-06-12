# myfin/finance/load_new_txs/load_new_txs.py
"""
Load new transactions for an account.

Account directory structure:
    - new_csvs (original csv files not needing pre-processing)
    - new_pre_csvs (originals needing processing to csvs, eg pdfs)
    - temp_csvs (csvs made by processing new_pre_csvs)
    - old_originals (new_csvs or new_pre_csvs after loading)

Begins with the existing tx_db (and optional cat_db external map of
item names to categories).

Looks for a 'prep.py' file to execute, to make csvs
  - originals in new_pre_csvs/
  - save results in temp_csvs/
  - move originals to old_originals/
  
Processes csvs calling process_new_txs_csv() to make a df of new txs

Appends the new txs df to tx_db and writes tx_db to disk
"""

from shutil import move
from pathlib import Path
import subprocess
import pandas as pd

from mylogger import get_filelog

# imports from this directory
from .process_new_txs_csv import process_new_txs_csv
from .append_to_tx_db import append_to_tx_db
from .archive_tx_db import archive_tx_db


def load_new_txs(acc_path, return_tx_db=False, write_out_tx_db=True,
                 move_new_txs=True, delete_temp_csvs=True):

    """
    Load the new transactions for the passed account.

    Appends the new txs df to tx_db and writes tx_db to disk
    Moves originals from new_csvs/ to old_originals/
    Deletes temp_csvs/

    Optionally returns the tx_db, and does not move files or write to disk.
    """

    # PREPARATION
    acc_path = Path(acc_path).absolute()

    if 'tx_accounts' not in str(acc_path):
        print(f'no "tx_accounts" found in {acc_path}'
              f'- does not look like a path')
        return None

    main_dir = acc_path.parents[1]
    logger = get_filelog(main_dir / 'log.txt')
    logger.info('------ calling load_new_txs() for {acc_path.name} ------')

    tx_db = pd.read_csv(main_dir / 'tx_db.csv', index_col='date')
    tx_db.index = pd.to_datetime(tx_db.index)

    cat_db = pd.read_csv(main_dir / 'cat_db.csv', index_col='_item')

    # run any prep.py to process pre-csv input files
    if ((acc_path / 'prep.py').exists() and
            list((acc_path / 'new_pre_csvs').iterdir())):

        subprocess.run(['python3', acc_path / 'prep.py', acc_path])
        # process_non_csv_originals(acc_path / 'new_pre_csvs')
        logger.info('processed pre_csvs')

    # get files ready for loading
    files_to_process = get_files_to_process(acc_path, logger)

    if files_to_process is None:
        print('no new files found')
        logger.info(f'found no new csvs to process')
        return None

    # MAIN LOOP: get df for each file of new txs, and append to tx_db
    new_tx_count = 0
    for csv_file in files_to_process:
        df = process_new_txs_csv(csv_file, tx_db, cat_db)
        tx_db = append_to_tx_db(df, tx_db)
        logger.info('appended to tx_db')
        new_tx_count += len(df)

    logger.info(f'--> Total new txs for {acc_path.name}: {new_tx_count}')


    # CLEANING UP
    if write_out_tx_db:
        tx_db.to_csv(main_dir / 'tx_db.csv')
        logger.info(f'writing out to {main_dir / "tx_db.csv"}')

        archive_tx_db(proj_path=main_dir, annotation='loaded_' + acc_path.name)
        logger.info(f'archived tx_db')

    else:
        logger.info(f'not writing out')


    if move_new_txs:
        for file in (acc_path / 'new_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)
            logger.info(f'moved {file} to'
                        f'{acc_path / "old_originals" / file.name}')

        for file in (acc_path / 'new_pre_csvs').iterdir():
            move(file, acc_path / 'old_originals' / file.name)


    if delete_temp_csvs and (acc_path / 'temp_csvs').exists():
        for file in (acc_path / 'temp_csvs').iterdir():
            file.unlink()


    if return_tx_db:
        return tx_db


def get_files_to_process(acc_path, logger=None):
    """
    Looks for files to process, including in new_csvs/ and temp_csvs/.

    Returns a list of Path objects ready for loading.
    """

    acc_path = Path(acc_path)
    files_to_process = None

    if (acc_path / 'new_csvs').exists():
        new_csv_paths = list((acc_path / 'new_csvs').iterdir())
        if new_csv_paths:
            files_to_process = new_csv_paths
            if logger is not None:
                logger.info(f'found {len(new_csv_paths)} files in new_csvs')
        else:
            if logger is not None:
                logger.info(f'found no new csvs to process')

    if (acc_path / 'temp_csvs').exists():
        temp_csv_paths = list((acc_path / 'temp_csvs').iterdir())
        if temp_csv_paths:
            files_to_process = temp_csv_paths
            if logger is not None:
                logger.info('found {len(temp_csv_paths)} files in temp_csvs')
        else:
            if logger is not None:
                logger.info(f'found no new csvs to process')

    return files_to_process
