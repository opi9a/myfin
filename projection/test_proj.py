import pytest
from copy import deepcopy
from pprint import pprint
import pandas as pd

import projection

@pytest.fixture
def base_eras():
    in_list = [
        {
            'start': pd.Period('1-2000'),
            'freq': 3,
            'repeats': 4,
            'last': pd.Period('10-2000'),
            'end': pd.Period('12-2000'),
        },

        {
            'start': pd.Period('1-2001'),
            'freq': 2,
            'repeats': 6,
            'last': pd.Period('11-2001'),
            'end': pd.Period('12-2001'),
        },

        {
            'start': pd.Period('1-2002'),
            'freq': 6,
            'repeats': 2,
            'last': pd.Period('7-2002'),
            'end': pd.Period('12-2002'),
        }
    ]

    return in_list

        
def test_in_era(base_eras):

    for i, row in enumerate(base_eras):
        print(f'in row {i}')
        for test_var in row:
            t = deepcopy(base_eras)
            print(f'\n---> setting {test_var} to None')
            t[i][test_var] = None

            out = projection.make_eras(t)
            compare(base_eras, out, test_var)


def test_inner(base_eras):

    for only_key in ['freq', 'repeats']:
        print(f'trying with only {only_key} in row 1, ', end='')
        only_val = base_eras[1][only_key]
        print(f'value is {only_val}')
        t = deepcopy(base_eras)
        t[1] = {only_key: only_val}
        print(f'new row 1 is {t[1]}')

        out = projection.make_eras(t)
        for var in out[1]:
            compare(base_eras, out, t[0].keys())


def compare(base_eras, test_eras, vars_to_print):
    if isinstance(vars_to_print, str):
        vars_to_print = [vars_to_print]
    for i, row in enumerate(base_eras):
        for var in row:
            if var in vars_to_print:
                print(f'row[{(str(i)+"] "+var).ljust(12)}{test_eras[i][var]}'
                      f': {base_eras[i][var]}')
            assert test_eras[i][var] == base_eras[i][var]


