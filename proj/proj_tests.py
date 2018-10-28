import pytest
from copy import deepcopy
import pandas as pd

import projection

@pytest.fixture
def single_era():
    in_list = [
        {
            'start': pd.Period('1-2000'),
            'freq': 3,
            'repeats': 4,
            'last': pd.Period('1-2001'),
            'end': pd.Period('3-2001'),
        }
    ]

    return in_list

def test_in_era(single_era):

    for i, row in enumerate(single_era):
        for var in row:
            t = deepcopy(single_era)
            t[i][var] = None
            out = projection.make_stream(t)

            for i, row in enumerate(single_era):
                for var in row:
                    print('testing', var)
                    print(f'{(str(i)+" "+var).ljust(12)}{out[i][var]}'
                          f': {single_era[i][var]}')
                    assert out[i][var] == single_era[i][var]


