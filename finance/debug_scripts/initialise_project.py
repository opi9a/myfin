# myfin/finance/debug_scripts/initialise_project.py

"""
Perhaps obsolete but should still work and may still be useful.

Will need to sort imports
"""

def initialise_project(proj_name, overwrite_existing=False,
                       parent_dir=None,
                       cat_db_to_import=None):

    """Required structure:

        proj_name/
        --- tx_db.csv
        --- cat_db.csv
        --- unknowns_db.csv
        --- fuzzy_db.csv
        --- log.txt
        --- tx_accounts/
        
        The csv files to contain column headings and index as appropriate, 
        but no rows.
    """

    # open a log list
    loglist = []

    # start from wherever called and make a directory with proj_name
    if parent_dir is None:
        parent_dir = os.getcwd()
    print('\ninitialising project in dir:', parent_dir)
    if not os.path.exists(proj_name):
        print('trying to create', proj_name)
        os.mkdir(proj_name)
    elif overwrite_existing:
        print(proj_name, 'exists already, overwriting it')
        rmtree(proj_name)
        os.mkdir(proj_name)
    else:
        print("A project with that name already exists in this directory.\
              pass 'overwrite_existing=True' to overwrite it")
        return 1

    os.chdir(proj_name)

    # make log first
    with open('log.txt', 'w') as f:
        f.write(tstamp() + 'initialising new project ' + proj_name + '\n')

    # handy set of columns 
    db_columns=['_item', 'accX', 'accY']

    # tx_db
    ind = pd.DatetimeIndex(start='1/1/1970', periods=0, freq='D', name='date')
    df = pd.DataFrame(columns=TX_DB_COLUMNS, index=ind)
    df.to_csv('tx_db.csv', index=True)
    addlog(loglist, 'made empty tx_db.csv')

    # cat_db
    if cat_db_to_import is not None:
        cat_db_to_import = os.path.join('..', cat_db_to_import)
        copyfile(cat_db_to_import, 'cat_db.csv')
        addlog(loglist, 'imported cat_db from' + cat_db_to_import)

    else:
        pd.DataFrame(columns=db_columns).to_csv('cat_db.csv', index=False)
        addlog(loglist, 'made empty cat_db.csv')

    # tx_accounts
    os.mkdir('tx_accounts')
    addlog(loglist, 'made empty tx_accounts directory')

    # unknowns_db
    pd.DataFrame(columns=db_columns).to_csv('unknowns_db.csv', index=False)
    addlog(loglist, 'made empty unknowns_db.csv')
 
    # fuzzy_db
    db_columns.append('status')
    pd.DataFrame(columns=db_columns).to_csv('fuzzy_db.csv', index=False)
    addlog(loglist, 'made empty fuzzy_db.csv')

    # write out log
    writelog(loglist)

    os.chdir(parent_dir)

    return os.path.abspath(proj_name)

