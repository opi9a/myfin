from pathlib import Path
import json
import pandas as pd

def load_new_csv_files(acc_path):

    acc_path = Path(acc_path)
    dfs = []

    for new_txs_file in (acc_path / 'new_csvs').iterdir():
        new_txs_df = pd.read_csv(new_txs_file)
        new_txs_df['source'] = new_txs_file.name
        dfs.append(new_txs_df)
    df = pd.concat(dfs)
    with open(acc_path / 'parser.json', 'r') as fp:
        parser = json.load(fp)

    df = format_new_txs(df, account_name=acc_path.name, parser=parser)
    df['ts'] = pd.Timestamp(pd.datetime.now())
    return df.sort_values(['date', 'ITEM'])


def format_new_txs(new_tx_df, account_name, parser):

    """Return a tx_df in standard format, with date index,
    and columns: 'date', 'ITEM', '_item', 'net_amt', 'balance', 'source'

    new_tx_df    : a df with transactions data

    account_name : name of the account, for assignation in the 'from' and
                   'to' columns

    parser       : dict with instructions for processing the raw tx file

                    - 'input_type' : 'credit_debit' or 'net_amt'

                    - 'date_format': eg "%d/%m/%Y"

                    - 'map'        : dict of map for column labels
                                     (new labels are keys, old are values)

                    - 'debit_sign' : are debits shown as negative
                                     or positive numbers? (for net_amt inputs)
                                     - default is 'positive'

                 - mapping must cover following columns (i.e. new labels):

                       - net_amt: ['date', 'accX', 'accY', 'net_amt', 'ITEM']

                       - credit_debit: 'debit_amt', 'credit_amt'
                         replace 'net_amt'

                 - may optionally provide a mapping for 'balance'

    """

    # check parser matches input df
    matches = {col: (col in new_tx_df.columns)
                   for col in parser['map'].values()}
    if not all(matches.values()):
        print('parser map does not match new_tx_df columns, so quitting')
        print('parser map values:', sorted(list(parser['map'].values())))
        print('new_tx_df.columns', sorted(list(new_tx_df.columns)))

        return

    # organise columns using parser, and add '_item' column
    df = new_tx_df[list(parser['map'].values())].copy()
    df.columns = parser['map'].keys()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    df['_item'] = df['ITEM'].str.lower().str.strip() 

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        df['debit_amt'] = pd.to_numeric(df['debit_amt'], errors='coerce')
        df['credit_amt'] = pd.to_numeric(df['credit_amt'], errors='coerce')

        df['net_amt'] = (df['debit_amt']
                             .subtract(df['credit_amt'], fill_value=0))

    if parser.get('debit_sign', 'positive') == 'positive':
        df['net_amt'] *= -1
        
    cols = ['ITEM', '_item', 'net_amt']

    if 'y_amt' in parser['map']:
        cols.append('y_amt')

    if 'balance' in parser['map']:
        cols.append('balance')

    # need to sort 'source' attribution when move to prep.py for all accs
    if 'source' in new_tx_df.columns:
        df['source'] = new_tx_df['source'].values
        cols.append('source')

    return df[cols]


def dev_format_new_txs(new_txs_csv_dir_path, parser):

    """
    Return a tx_df in standard format, with date index,
    and columns: 'date', 'ITEM', '_item', 'net_amt', 'balance', 'source'

    new_txs_csv_dir_path : path to dir with transactions data csvs

    parser               : dict with instructions for processing raw tx csvs

                            - 'input_type' : 'credit_debit' or 'net_amt'

                            - 'date_format': eg "%d/%m/%Y"

                            - 'map'        : dict of map for column labels
                                                { new label: old label, .. }

                            - 'debit_sign' : are debits shown as negative or
                                             positive in raw csv? (if net_amts)
                                             - default is 'positive'

                         - mapping must cover following cols (i.e. new labels):

                               - for net_amt type:
                                   ['date', 'accX', 'accY', 'ITEM', 'net_amt']

                               - for credit_debit type:
                                   ['date', 'accX', 'accY', 'ITEM',
                                    'debit_amt', 'credit_amt']

                         - may optionally provide a mapping for 'balance'

                         - todo mapping for 'y_amt'

    """

    account_name = new_txs_csv_dir_path.parts[-2] 

    new_tx_files = [x for x in new_txs_csv_dir_path.iterdir()
                    if x.name.endswith('.csv')]

    new_tx_dfs = []

    for f in new_tx_files:
        new_tx_df = pd.read_csv(f)
        new_tx_df['source'] = f.name
        new_tx_dfs.append(new_tx_df)

    df = pd.concat(new_tx_dfs)
    df = format_new_txs(df, account_name, parser)
    
    # check parser matches input df
    matches = {col: (col in new_tx_df.columns)
                   for col in parser['map'].values()}
    if not all(matches.values()):
        print('parser map does not match new_tx_df columns, so quitting')
        print('parser map values:', sorted(list(parser['map'].values())))
        print('new_tx_df.columns', sorted(list(new_tx_df.columns)))

        return

    # organise columns using parser, and add '_item' column
    df = new_tx_df[list(parser['map'].values())].copy()
    df.columns = parser['map'].keys()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    df['_item'] = df['ITEM'].str.lower().str.strip() 

    # for credit_debits, make a 'net_amt' column
    if parser['input_type'] == 'credit_debit':
        df['debit_amt'] = pd.to_numeric(df['debit_amt'], errors='coerce')
        df['credit_amt'] = pd.to_numeric(df['credit_amt'], errors='coerce')

        df['net_amt'] = (df['debit_amt']
                             .subtract(df['credit_amt'], fill_value=0))

    if parser.get('debit_sign', 'positive') == 'positive':
        df['net_amt'] *= -1
        
    cols = ['ITEM', '_item', 'net_amt']

    if 'balance' in parser['map']:
        cols.append('balance')

    # need to sort 'source' attribution when move to prep.py for all accs
    if 'source' in new_tx_df.columns:
        df['source'] = new_tx_df['source'].values
        cols.append('source')

    return df[cols]


