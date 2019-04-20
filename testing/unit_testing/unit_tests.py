from pathlib import Path
import pandas as pd
from shutil import rmtree
import pytest
from finance.update_dbs import update_all_dbs
from finance.load_new_txs import db_compare, load_new
from finance.init_scripts import (initialise_project, populate_test_project,
                                  xmake_targets, check_seed)

seed_df_path = Path('~/shared/projects/myfin/testing/'
                    'data_setup_test/test_csv_generator.csv').expanduser()


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

    if Path(proj_name).exists():
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


def test_load_new_txs(new_project_fx):
    proj_dir, targets = new_project_fx

    # run function testing load procedure
    load_new(proj_dir)
    check_disk_dbs(Path(proj_dir), targets, 'loaded')


def test_update_all_dbs():
    """
    Run the update_all_dbs() function against a known set of input dbs,
    and check for generation of correct output dbs
    """

    INPUT_DBS_PATH = Path('~/shared/projects/myfin/testing/'
                          'unit_testing/update_dbs/input_dbs').expanduser()

    TARGET_DBS_PATH = Path('~/shared/projects/myfin/testing/'
                          'unit_testing/update_dbs/target_dbs').expanduser()

    print('\nTesting update_all_dbs()\n')

    # make a dictionary of paths to the input dbs
    paths_dict = {}
    for path in INPUT_DBS_PATH.iterdir():
        db = path.name.split('.')[0]
        paths_dict[db] = path

    # call function with parameters to ensure it returns not writes dbs
    test_dbs = update_all_dbs(paths_dict,
                              return_dbs=True,
                              write_out_dbs=False)

    # get the target_dbs for comparison
    target_dbs = {}
    for path in TARGET_DBS_PATH.iterdir():
        db = path.name.split('.')[0]
        target_dbs[db] = pd.read_csv(path, index_col=test_dbs[db].index.name)

    # run the comparison
    for db in target_dbs:
        print(db.ljust(20), end="")
        db_compare(target_dbs[db], test_dbs[db], assertion=True)

###################### helper functions #######################################

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

#------------ not done yet ------------#

def test_add_target_acc_col():
	pass

def test_apply_parser():
	pass

def test_assign_targets():
	pass

def test_balance_continuum():
	pass

def test_check_df():
	pass

def test_db_compare():
	pass

def test_execute_prep_script():
	pass

def test_format_new_txs():
	pass

def test_get_dbs():
	pass

def test_load_new():
	pass

def test_make_parser():
	pass

def test_parse_new_txs():
	pass

def test_pick_match():
	pass

def test_tidy():
	pass

def test_trim_df():
	pass

def test_trim_overlap():
	pass

def test_update_fuzzies():
	pass

def test_update_tx_db():
	pass

def test_update_unknowns():
	pass

