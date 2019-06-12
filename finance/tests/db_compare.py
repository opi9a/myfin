# myfin/finance/tests/db_compare.py

from termcolor import cprint

from .test_helpers import print_title

def db_compare(test, target, db_name=None,
               cols_to_ignore=['id', 'source', 'mode'],
               index_cols=['date', '_item', 'accX'],
               show_even_if_equal=False,
               assertion=False):
    """
    Compares two dataframes.

    First naively applies target.equals(test), returns True
    (and asserts True) if True.

    If not, compare columns and indexes.

    Finally compare common core (common index and columns)

    To make unique indexes probably want to set indexes to eg
    ['date', '_item', 'accX']

    Passing cols_to_ignore affects only equality test - the cols will still
    be printed and compared if dfs not equal
    """

    # get rid of pesky nans which compare unequal
    test = test.copy().fillna("BLANK").sort_index()
    target = target.copy().fillna("BLANK").sort_index()

    # make sure columns same 
    if set(test.columns) != set(target.columns):
        print('test and target have different columns')
        _diff_columns(test, target)
        return

    # apply index cols if passed (and if present in df)
    if index_cols is not None:
        cols_present = [c for c in index_cols if c in test.columns]
        test = test.reset_index().set_index(cols_present, drop=True)
        target = target.reset_index().set_index(cols_present, drop=True)

    # get columns in same order (based arbitrarily on test)
    target = target[test.columns]

    if db_name is not None:
        print_title(db_name.upper())

    if cols_to_ignore:
        print('ignoring columns', cols_to_ignore, end=" ")
    else:
        print('ignoring no columns', end=" ")

    print(target.shape, "vs", test.shape, end=": ")

    # simple equality test
    cols_to_try = test.columns.difference(cols_to_ignore)
    if target[cols_to_try].equals(test[cols_to_try]):
        cprint('dbs equal by df.equals()', color='green', attrs=['bold'])
        if assertion:
            assert True
            return True

        if not show_even_if_equal:
            return True

    else:
        cprint('NOT EQUAL', color='red', attrs=['bold'])

    print_title(str(db_name) + ':  INEQUALITY ANALYSIS')
    print('\ntest df:')
    print(test)
    print('\ntarget df:')
    print(target)

    # COMPARE INDEXES
    if tuple(test.index) != tuple(target.index):
        print_title(str(db_name) + ':  INDEX DIFFS')
        print('\nNon-identical indexes')
        diff_indexes(test, target)
    else:
        print('indexes are the same')
    # Print df comparisons / differences
    print_title(str(db_name) + ':  DF COMPARISONS')

    # mask - NB a superset / union with all rows and columns
    mask = test[cols_to_try].eq(target[cols_to_try])

    # print the result of eq() but using '-' and 'X' markers
    mask_diff = mask.copy()
    mask_diff = mask_diff.where(mask, other='X')
    mask_diff = mask_diff.where(~mask, other='-')
    print('\nComparison over union')
    print(mask_diff)

    #call diffs func for row-by-row comparison - only if unique indices
    if test.index.is_unique and target.index.is_unique:
        print_title(str(db_name) + ':  TEST')
        print()
        show_df_diffs(test[cols_to_try], target[cols_to_try])
        print_title(str(db_name) + ':  TARGET')
        print()
        show_df_diffs(target[cols_to_try], test[cols_to_try])
    else:
        print('\nNot comparing row-by-row as indices not both unique')

    print_title()

    if assertion:
        assert False

    return False


def strftime_date_index(df, strf_format='%d-%m-%y'):
    """
    Converts a level of a multi-index labelled 'date' to strings
    using strftime.
    """

    orig_names = df.index.names

    df = df.reset_index()
    df['date'] = df['date'].apply(lambda x: x.strftime(strf_format))

    return df.set_index(orig_names)


def _diff_columns(test, target):
    """
    Compares the columns of two dfs, printing differences
    """

    print('\ntest columns', sorted(list(test.columns)))
    print('\ntarget columns', sorted(list(target.columns)))

    test_not_target = test.columns.difference(target.columns)
    target_not_test = target.columns.difference(test.columns)

    if not test_not_target.empty:
        print('\nin test not target:', test_not_target.values)

    if not target_not_test.empty:
        print('\nin target not test:', target_not_test.values)


def diff_indexes(df1, df2):
    """
    Compare each, highlight differences

    ONLY WORKING FOR DATE INDICES RIGHT NOW
    """

    pad = 50
    ind1 = tuple(strftime_date_index(df1).index)
    ind2 = tuple(strftime_date_index(df2).index)

    print('\nTEST'.ljust(pad) + 'TARGET')

    # get superset
    superset = sorted(list(set(ind1).union(set(ind2))), key=lambda x: x[0])

    out = {}

    for elem in superset:
        counts = {'ind1': ind1.count(elem), 'ind2': ind2.count(elem)}

        while max(counts.values()):
            for ind in counts:
                if counts[ind]:
                    counts[ind] -= 1
                    out.setdefault(ind, []).append(", ".join(elem))
                else:
                    out.setdefault(ind, []).append(None)

    for i in range(len(out['ind1'])):
        if out['ind1'][i] == out['ind2'][i]:
            color = None
        else:
            color = 'red'

        for ind in out:
            if out[ind][i] is None:
                cprint(('-' * (pad - 9)).ljust(pad), color=color, end="")
            else:
                cprint(out[ind][i].ljust(pad), color=color, end="")

        print("")


def show_df_diffs(x, y, verbose=False):
    """
    Attempts cell-by-cell comparison of dfs.

    Only works if row indexes are unique
    """

    pad = 20
    
    df_out = x.copy()

    for i, row in enumerate(x.index):
        if verbose: print_title()
        if verbose: print(f'\nin row {i}:'.ljust(pad), row)

        if not row in y.index:
            if verbose: print('row not found in y\n')
            continue

        for j, col in enumerate(y.columns):
            if verbose: print(f' -in col {i}:'.ljust(pad), col)

            if not col in y.columns:
                if verbose: print('col not found in y\n')
                continue
            
            if verbose: print(' -- x_val:'.ljust(pad), x.loc[row, col])
            if verbose: print(' -- y_val:'.ljust(pad), y.loc[row, col])

            if y.loc[row, col] == x.loc[row, col]:
                if verbose: print('ok\n')
                df_out.loc[row, col] = '-'
            else:
                if verbose: print('NOT EQUAL\n')

    print(df_out)

