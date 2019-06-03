# myfin/finance/testing/test_update_dbs.py

from pathlib import Path

from finance.update_dbs import update_dbs_after_changes
from finance.update_dbs import update_after_changed_unknowns
from finance.update_dbs import update_after_changed_fuzzy

from .test_helpers import (db_compare,
                          make_dfs_from_master_xls,
                          make_dbs_from_master_dfs,
                          print_db_dicts, print_title)

MASTER_XLSX_PATH = ('~/shared/projects/myfin/'
                    'testing/xlsx_masters/update_dbs_masters/')


def test_all_update(master_xls_dir=MASTER_XLSX_PATH):
    """
    Helper which runs test for updating for changes in both fuzzy_db and
    unknowns_db.
    """

    master_xls_dir = Path(master_xls_dir)

    for db in ['unknowns_db', 'fuzzy_db']:
        master_path = Path(master_xls_dir / (db + '.xlsx'))

        test_update_dbs(db, master_path)


def test_update_dbs(changed_db_name, master_xls_path, show_dbs=False,
                    ignore_cols=['id', 'mode', 'source']):
    """
    Makes a set of input and target dbs.  
    Then runs the input dbs through update function (specified with
        changed_db_name)

    Compares result with target dbs
    """


    # get test and targets from master path, and by calling the function
    dfs = make_dfs_from_master_xls(master_xls_path)
    dbs = make_dbs_from_master_dfs(dfs)

    dbs['test'] = update_dbs_after_changes(changed_db_name=changed_db_name,
                                           dbs=dbs['input'],
                                           return_dbs=True,
                                           write_out_dbs=False)

    if show_dbs:
        print_db_dicts(dbs)
        print()
        
    # run the comparison
    print()
    print_title(f'After changes in {changed_db_name}'.upper(),
                attrs=['bold'])

    for db in dbs['test']:
        db_compare(dbs['test'][db], dbs['target'][db], db_name=db,
                   ignore_cols=ignore_cols, assertion=True)


if __name__ == '__main__':
    test_all_update()
