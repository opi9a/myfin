# myfin/finance/load_new_txs/process_new_txs_csv.py
"""
Loads csvs to a pandas df
  - from either new_csvs/ or temp_csvs/

Parses and assigns standard column headings:
  - 'date', 'ITEM', 'source'
  - either:
      - 'net_amt', or
      - 'credit_amt' and 'debit_amt'
  - optionally: 'y_amt', 'balance'

Calculates 'net_amt' if required

Adds other columns:
    - makes standardised '_item' field (lower case, stripped)
    - adds account name ('accX')

Trims overlaps vs tx_db, adding an 'id' field

Adds an 'accY' target account column, by either:
  - looking up in tx_db or cat_db
  - making a fuzzy match
  - todo: applying previously defined rules
  - leaving 'unknown'

Adds a 'mode' column recording how 'accY' was assigned
  - confirmed means has been verified after load, or was looked up
    from a tx with 'mode' == confirmed
  - fuzzy means was assigned by fuzzy match, or was looked up
    from a tx with 'mode' == fuzzy
  - unknown means could not be assigned by lookup or fuzzy match
  - TODO: mode of 'special' is not copied in lookup or fuzzy match
"""

import pandas as pd

from mylogger import get_filelog
from pathlib import Path

from .apply_parser import apply_parser
from .trim_df import trim_df
from .clean_tx_df import clean_tx_df
from .get_accYs_modes import get_accYs_modes


def process_new_txs_csv(csv_file, tx_db, cat_db=None):
    """
    Load and process a individual csv_file, using tx_db and cat_db
    as sources for assigning accY.

    Return a df ready for appending to tx_db.
    """
    csv_file = Path(csv_file)
    acc_path = csv_file.parents[1]
    main_dir = acc_path.parents[1]

    if not isinstance(tx_db.index, pd.core.indexes.datetimes.DatetimeIndex):
        tx_db.index = pd.DatetimeIndex(tx_db.index)

    logger = get_filelog(main_dir / 'log.txt')
    logger.info(f'------ processing {csv_file.name} ------')

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

    df = trim_df(df, tx_db)
    logger.info(f'after trim_df, {len(df)} txs')

    accYs, modes = get_accYs_modes(df['_item'],
                                   acc_path.name, tx_db, cat_db)
    df['accY'] = accYs
    df['mode'] = modes

    # TODO standardise column types etc
    return df
