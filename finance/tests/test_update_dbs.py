# myfin/finance/tests/test_update_dbs.py

from pathlib import Path

from finance.update_dbs import update_dbs_after_changes
from finance.update_dbs import update_after_changed_unknowns
from finance.update_dbs import update_after_changed_fuzzy

from .db_compare import db_compare
from .make_test_constructs import make_dbs_from_master_xlsx
from .test_helpers import print_db_dicts, print_title

MASTER_XLSX_PATH = ('~/shared/projects/myfin/'
                    'testing/xlsx_masters/update_dbs_masters/')


def test_all_update(master_xls_dir=MASTER_XLSX_PATH):
    """
    Helper which runs test for updating for changes in both fuzzy_db and
    unknowns_db.
    """

    print_title('test_all_update()', borders=True, attrs=['bold'],
                                     color='blue', char='-')

    master_xls_dir = Path(master_xls_dir)

    for db in ['unknowns_db', 'fuzzy_db']:
        master_path = Path(master_xls_dir / (db + '.xlsx'))

        test_update_dbs(db, master_path)


def test_update_dbs(changed_db_name, master_xls_path, show_dbs=False,
                    cols_to_ignore=['id', 'mode', 'source'], 
                    assertion=True):
    """
    Makes a set of input and target dbs.  
    Then runs the input dbs through update function (specified with
        changed_db_name)

    Compares result with target dbs
    """


    # get test and targets from master path, and by calling the function
    dbs = make_dbs_from_master_xlsx(master_xls_path)

    dbs['test'] = update_dbs_after_changes(changed_db_name=changed_db_name,
                                           dbs=dbs['input'],
                                           return_dbs=True,
                                           write_out_dbs=False)

    if show_dbs:
        print_db_dicts(dbs)
        print()
        
    # run the comparison
    print_title(f'After changes in {changed_db_name}'.upper(),
                attrs=['bold'])

    for db in dbs['test']:
        db_compare(dbs['test'][db], dbs['target'][db], db_name=db,
                   cols_to_ignore=cols_to_ignore, assertion=assertion)


if __name__ == '__main__':
    test_all_update()
