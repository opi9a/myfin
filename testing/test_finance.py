import pandas as pd
import numpy as np
import os
from shutil import rmtree
from pprint import pprint
import pytest

import finance.load_new_txs as lntx
from finance.load_new_txs import _prtitle, _db_compare, load_new

from finance.init_scripts import (initialise_project, populate_test_project,
                                  xmake_targets, check_seed)
from finance.update_dbs import new_updater

seed_df_path = '~/programming/python/myfin/testing/data_setup_test/test_csv_generator.csv'


#--------------- FIXTURES AND CONSTANTS ---------------------------------------

@pytest.fixture
def new_project_fx(scope="module"):
    """Create a new project file structure, with two tx_account folders.
    Populates with test data in the seed_df.
    Yields the path of the project root.
    """
    proj_name = 'new_test_project'

    if check_seed(seed_df_path):
        print('check_seed fail')
        return 1

    if os.path.exists(proj_name):
        print('found an existing project named', proj_name, '- removing')
        rmtree(proj_name)

    print('\nsetting up fixture')
    new_proj_path = initialise_project(proj_name, overwrite_existing=False)

    seed_df = pd.read_csv(seed_df_path, parse_dates=['date'], dayfirst=True,
                                                             index_col='date')
    populate_test_project(seed_df, new_proj_path)

    yield new_proj_path
    # return new_proj_path

    # teardown
    print('\ntearing down fixture')
    rmtree(new_proj_path)

proj_directory = {'tx_db.csv',
                  'cat_db.csv',
                  'unknowns_db.csv',
                  'fuzzy_db.csv',
                  'log.txt',
                  'tx_accounts',
                 }


#-------------- MAIN TEST SEQUENCE --------------------------------------------


def test_main_seq(new_project_fx):
    # create fixture, yielding path to root of project file structure
    proj_dir = new_project_fx

    # note where we start, then move to the test project directory
    init_dir = os.getcwd()
    os.chdir(proj_dir)

    # load seed df
    seed_df = pd.read_csv(seed_df_path, parse_dates=['date'], dayfirst=True,
                                                             index_col='date')
    seed_df = seed_df.sort_values('date')
    seed_df['_item'] = seed_df['ITEM'].str.lower().str.strip()
    print('\n---> seed_df loaded\n', seed_df)

    # generate targets (what the seed_df should yield)
    targets = xmake_targets(seed_df_path) 
    print('targets loaded:')
    for stage in targets:
        for db in targets[stage]:
            print('\n--->' + stage + " / " + db)
            print(targets[stage][db])

    # run function testing load procedure
    load_new(seed_df, targets)

    # make some changes to unknowns_db and fuzzy_db, acc to seed_df
    # get tuples to changeo
    make_db_changes(seed_df)

    # run function testing update procedure
    run_updater(seed_df, targets)

    # go back where we started
    os.chdir(init_dir)

    print('\nnew test project in main?:', os.path.exists('new_test_project'))

# def test_x():
    # print('\nnew test project in test_x?:', os.path.exists('new_test_project'))
    # # print('/ntx_db\n', pd.read_csv('new_test_project/tx_db.csv'))


#-------------- sub functions -------------------------------------------------

def make_db_changes(seed_df):
    """make changes to the dbs on disc, simulating user manual editing.
    Changes are defined in the 'update_action' column of the seed df.
    """

    # pattern:
        # get (_item, accX) tuples that need changing (tuples_to_change):
          # eg rows in unknowns where update_action in seed is not null
        # get new values for those from seed_df['update_action']
            # issue here is that may be duplicates of these, so need to make
            # sure the seed_df is processed to get unique tuples in index
        # set target db accYs to new values, eg:
            # unknowns_db.loc[tuples, 'accY'] = newvals

    _prtitle('Making changes to dbs to simulate manual curation')

    # first get a version of seed_df indexed by _item, accX tuples
    df_tup = seed_df.copy().reset_index().set_index(['_item', 'accX'])
    df_tup = df_tup.loc[~df_tup['update_action'].isnull()]
    df_tup = lntx.tidy(df_tup['update_action'])
    print('\ndf_tup: tidy version of seed_df, with update actions\n', df_tup)

    # 1. unknowns:
        # change: anything in unknowns with an update action in seed_df
        # - overwrite with corresponding value in seed_df[update_action]

    unknowns_db = (pd.read_csv('unknowns_db.csv', index_col='_item')
                           .reset_index().set_index(['_item', 'accX']))
    print('\nChanging unknowns_db.  Original:\n', unknowns_db)

    # build a mask to get the tuples to change
    mask1 = df_tup.index.isin(unknowns_db.index)
    mask2 = ~df_tup['update_action'].isnull()
    mask = mask1 & mask2
    tuples_to_change = df_tup.loc[mask].index
    print('\ntuples to change (indexer)\n', tuple(tuples_to_change))

    new_vals = df_tup.loc[mask]
    print('\nnew_vals\n', new_vals)

    unknowns_db.loc[tuples_to_change, 'accY'] = new_vals.values
    print('\nunknowns db after change\n', unknowns_db)

    unknowns_db.reset_index().set_index('_item').to_csv('unknowns_db.csv')

    # anything in fuzzy_db with an action in seed_df[update_action]:
        # - overwrite with corresponding value in seed_df[update_action]
        
    fuzzy_db = (pd.read_csv('fuzzy_db.csv', index_col='_item')
                           .reset_index().set_index(['_item', 'accX']))
    print('\nChanging fuzzy_db.  Original:\n', fuzzy_db)

    mask = ~df_tup.loc[fuzzy_db.index, 'update_action'].isnull()
    tuples_to_change = (fuzzy_db.loc[mask].index)
    print('\ntuples to change (indexer)\n', tuple(tuples_to_change))

    new_vals = df_tup.loc[tuples_to_change, 'update_action']
    print('\nnew_vals\n', new_vals)

    fuzzy_db.loc[tuples_to_change, 'status'] = new_vals.values
    print('\nfuzzy db after change\n', fuzzy_db)

    fuzzy_db.reset_index().set_index('_item').to_csv('fuzzy_db.csv')



def run_updater(seed_df, targets):
    """test outputs of updater function
    """

    _prtitle('Running Updates')

    # print('\nunknowns_db before updating\n', pd.read_csv('unknowns_db.csv'))
    new_updater()
    # print('\nunknowns_db after updating\n', pd.read_csv('unknowns_db.csv'))

    print('\ntesting tx_db after update..', end='')
    tx_db = pd.read_csv('tx_db.csv', index_col='date', parse_dates=['date'])

    print('\nfull set of columns (not all kept for test)\n', tx_db.columns)

    test_cols = ['_item', 'accX', 'accY', 'net_amt']
    test = tx_db[test_cols].sort_index()
    target = targets['updated']['tx_db'][test_cols].copy().sort_index()  
    print('\ntest\n', test)
    print('\ntarget\n', target)

    _db_compare(target, test)



#---------- helper functions  ------------------------------------------------

# def test_temp(new_project_fx):
#     print('\nnew test project in test-temp?:', os.path.exists('new_test_project'))
#     print(os.listdir())
#     print(pd.read_csv('new_test_project/tx_db.csv'))


