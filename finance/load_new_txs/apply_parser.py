# myfin/finance/load_new_txs/apply_parser.py
"""
Single function to apply a parser to columns of a df
containing new transactions
"""

import json

from mylogger import get_filelog


def apply_parser(df, acc_path):
    """
    Loads parser from acc_path and applies to passed raw df.

    Also reverses net_amt sign if specified in parser.
    """

    logger = get_filelog(acc_path.parents[1] / 'log.txt')
    logger.info('calling apply_parser() for {acc_path.name}')

    parser = json.load((acc_path / 'parser.json').open())

    df = df[list(parser['map'].values())].copy()
    df.columns = parser['map'].keys()
    df['source'] = acc_path.name

    if ('net_amt' in df.columns and
            parser.get('debit_sign', 'negative') == 'positive'):
        df['net_amt'] *= -1
        logger.info(f'reversed net_amt sign')

    return df
