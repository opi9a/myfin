# ~/shared/projects/myfin/testing/test_finance.py
import pandas as pd
import numpy as np
import os
from pathlib import Path
from shutil import rmtree
from pprint import pprint
import pytest

import finance.load_new_txs as lntx
from finance.load_new_txs import _prtitle, _db_compare, load_new_test

from finance.init_scripts import (initialise_project, populate_test_project,
                                  xmake_targets, check_seed)
from finance.update_dbs import new_updater

seed_df_path = '~/shared/projects/myfin/testing/data_setup_test/test_csv_generator.csv'


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

    targets = xmake_targets(seed_df_path) 
    print('targets loaded:')
    for stage in targets:
        for db in targets[stage]:
            print('\n--->' + stage + " / " + db)
            print(targets[stage][db])

    yield new_proj_path, targets
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

def _new(new_project_fx):
    """
    In progress
    """

    main_dir = Path(new_project_fx)
    # load seed df
    seed_df = pd.read_csv(seed_df_path, parse_dates=['date'], dayfirst=True,
                                                             index_col='date')
    seed_df = seed_df.sort_values('date')
    seed_df['_item'] = seed_df['ITEM'].str.lower().str.strip()
    print('\n---> seed_df loaded\n', seed_df)

    # pass to load_new()
    # test results
    # make changes
    # test results

def test_main_seq(new_project_fx):
    # create fixture, yielding path to root of project file structure
    # and the targets (dfs generated for comparison if all works)

    proj_dir, targets = new_project_fx

    # note where we start, then move to the test project directory
    init_dir = os.getcwd()
    os.chdir(proj_dir)

    # load seed df
    seed_df = pd.read_csv(seed_df_path, parse_dates=['date'], dayfirst=True,
                                                             index_col='date')
    seed_df = seed_df.sort_values('date')
    seed_df['_item'] = seed_df['ITEM'].str.lower().str.strip()
    print('\n---> seed_df loaded\n', seed_df)

    # run function testing load procedure
    load_new_test(seed_df, targets)
    check_disk_dbs(Path(proj_dir), targets, 'loaded')

    # make some changes to unknowns_db and fuzzy_db, acc to seed_df
    # get tuples to changeo
    make_db_changes(seed_df)

    # run function testing update procedure
    run_updater(seed_df, targets)
    # the next check fails - I think because targets wrong
    # after update
    check_disk_dbs(Path(proj_dir), targets, 'updated')
    
    # go back where we started
    os.chdir(init_dir)

    print('\nnew test project in main?:', os.path.exists('new_test_project'))


def check_disk_dbs(main_dir, targets, stage):
    """
    tests if saved dbs are correct by comparing with targets
    """
    print('do final, path is', main_dir)
    tx_db = pd.read_csv(main_dir / 'tx_db.csv', parse_dates=['date'],
                                            dayfirst=True, index_col='date')

    print('target\n', targets[stage]['tx_db'])
    compare_target(stage, 'tx_db', tx_db, targets)

    fuzzy_db = pd.read_csv('fuzzy_db.csv', index_col='_item')
    compare_target(stage, 'fuzzy_db', fuzzy_db, targets)

    unknowns_db = pd.read_csv('unknowns_db.csv', index_col='_item')
    compare_target(stage, 'unknowns_db', unknowns_db, targets)


def compare_target(stage, dbname, df, targets):
    """helper function to put together tests for each db"""

    print('\n' + 'testing', dbname, '- at stage', stage)

    target_df = targets[stage][dbname]
    target_df = (target_df.sort_values(by=list(target_df
                                               .columns)).sort_index())
    test_df = df[target_df.columns].copy()
    test_df = test_df.sort_values(by=list(test_df.columns)).sort_index()

    print('\ntest df from csv\n', test_df)
    print('\ntarget df\n', target_df)

    assert target_df.equals(test_df)
    print(' ..OK******')
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

    # todo: add anything
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

