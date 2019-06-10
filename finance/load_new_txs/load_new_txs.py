# myfin/finance/load_new_txs/load_new_txs.py

from shutil import move
from pathlib import Path
import subprocess
import pandas as pd

from mylogger import get_filelog

# imports from this directory
from .apply_parser import apply_parser
from .trim_df import trim_df
from .clean_tx_df import clean_tx_df
from .get_accYs_modes import get_accYs_modes
from .append_to_tx_db import append_to_tx_db
from .archive_tx_db import archive_tx_db

def load_new_txs(acc_path, return_tx_db=False, write_out_tx_db=True,
                     move_new_txs=True, delete_temp_csvs=True):

    """

    **********
    CHANGING TO TX_DB_CENTRED:

    load_new_txs:
        - initially load tx_db only (no fuzzy_db or unknowns_db exist)
        - add_target_acc_col to use tx_db (and optional external cat_db)
          - use priority system to assign
        - append to tx_db only

    add_target_acc_col:
        apply to each new loaded tx, based on its '_item' and 'accX'
        def get_matches():
            get all exact matches first
            -> if no exact match, get all fuzzy matches
            return matches

        pick from matches
        ordering criteria:
            '_item' only, or 'accX' too
            mode value

    Priority system:
        Relates to weight of accY assignation for that tx
        Recorded in 'mode' col
        Initially assigned by add_target_acc_col
        Can be amended programmatically (with amendment of accY)
        (may be broadcast to many as part of amendment, but
         no automatic broadcasting / interdependencies. Cd add later.)

        Mode is vehicle for external information from assignment process:
            mode of originating* assignment, and possible extra state:
                fuzzy matching:
                    no extra state, just mode
                    (tho cd have eg scores)
                amendment:
                    extra state with confidence of amendment
                absence of either

            *NB mode is transitive:  reflect originating assignation,
             not whether this was direct or indirect.  Eg if find an
             existing fuzzy match, assign as fuzzy_matched, not
             distinguishing old_ and new_fuzzy_matched.

             Tho cd have a field for parent tx

        Use for:
            guiding future accY assignments by add_target_acc_col:
                by exact or fuzzy match
            selecting txs / assignations to amend (eg get all fuzzy matched)

        Modes: (make arbitrarily extensible
                 -> have a table dictating levels and rules?)

            unknown:  no match when loaded
                eg rule: do not use for matching

            fuzzy_matched: assigned by fuzzy match when loaded
                only useful for matching to increase efficiency,
                avoid a fuzzy match
                presume the confirmed source still there, and may be
                new confirmed sources, with this assignment not updated?

            confirmed0: (high category width)
                use for exact and fuzzy match
            confirmed1: (med category width)
                use for exact but not fuzzy match
            confirmed2: (low category width)
                do not use for matching (flag just for selection)

            new/existing confirmed?

    update_dbs:
        - only update tx_db obviously (ext cat_db?)
        - amend tx by tx, programmatically
            - eg with function taking 'id'
            - can therefore use rules, mass amends, fancy indexing etc

    rescan after changing?  Probably not.  In principle, rescan
    is just one of the things that can be done.

    bother with initial assignment, or just do rescans?  May as well
    do it and can always drop.  Acting on new txs feels logically effiient,
    will probably want to separate them out again after anyway.

    **********

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

    if 'tx_accounts' not in str(acc_path):
        print(f'no "tx_accounts" found in {acc_path}'
              f'- does not look like a path')
        return

    main_dir = acc_path.parents[1]
    logger = get_filelog(main_dir / 'log.txt')
    logger.info('------ calling load_new_txs() for %s ------', acc_path.name)

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
            logger.info('found %s files in temp_csvs', len(temp_csv_paths))
        else:
            logger.info(f'found no new csvs to process')

    else:
        print('no new files found')
        logger.info(f'found no new csvs to process')
        return

    # MAIN LOOP: build df of new txs; append txs to dbs as required
    new_tx_count = 0
    for csv_file in files_to_process:
        logger.info('------ processing %s ------', csv_file.name)

        df = pd.read_csv(csv_file)
        logger.info('loaded csv with %s txs', len(df))

        if (acc_path / 'parser.json').exists():
            print('calling apply_parser')
            df = apply_parser(df, acc_path)

        df = clean_tx_df(df)

        if not 'net_amt' in df.columns:
            df['net_amt'] = (df['credit_amt']
                             .subtract(df['debit_amt'], fill_value=0))
            logger.info('made net_amts')

        df['accX'] = acc_path.name
        df['_item'] = df['ITEM'].apply(lambda x: x.casefold().strip())

        df = trim_df(df, tx_db)
        logger.info('after trim_df, %s txs', len(df))

        accYs, modes = get_accYs_modes(df['_item'],
                                       acc_path.name, tx_db, cat_db)
        df['accY'] = accYs
        df['mode'] = modes


        # TODO standardise column types etc

        tx_db = append_to_tx_db(df, tx_db)
        logger.info('appended to tx_db')

        new_tx_count += len(df)

    logger.info('--> Total new txs for %s: %s', acc_path.name, new_tx_count)

    # CLEANING UP
    if write_out_tx_db:
        tx_db.to_csv(main_dir / 'tx_db.csv')
        logger.info(f'writing out to %s', main_dir / 'tx_db.csv')

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
