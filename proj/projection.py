import pandas as pd
import numpy as np
from pprint import pprint

from start import get_start
from calc_f import calc_f

"""
Build pd.Series of tx schemes in layers. Each series has a name, 
and meta data describing how it was created (which can be amended
so the series can be recreated with different parameters)

So need basic engine to translate an ordered series of instructions
into a series of txs.

Or just have a trajectory to which one-offs can be added

Eg wages:
    - start with a trajectory, such as:
        - £23k pa for 3 years rising at 5% pa
        - then jump to £30k, rising 3% pa for 5 yrs
        - then 40% reduction, but continue rising at 2% until retirement
        - at retirement fall to zero forever

So an instruction needs:
    - a start period
    - an amount, or a multiplier (or addition) to previous period
    - a growth rate

A trajectory also needs an end date of some kind, unless (default) 
continues indefinitely.


Want to be able to add elements, eg:
    - a one off tx:
        - amount, time
    - a series of txs:
        - over a certain period
        - at a certain frequency, eg every 4 months
        - with a certain growth rate
"""

def make_stream(in_list, _dbg=False):

    # copy over vars in in_list to eras
    eras = []
    vars = ['start', 'freq', 'last', 'repeats', 'end',
           'init_amt', 'gr']
    # , 'amt', 'gr', 'gr_freq']

    for row in in_list:
        era = {var: row.get(var, None) for var in vars}
        eras.append(era)

    # for each era, calc each missing var
    # - need to keep repeating until changes exhausted
    iters = 0; exhausted = False

    while not exhausted:
        if _dbg: print(f'\nIn iter {iters}..')
        iters += 1; exhausted = True

        for i, era in enumerate(eras):
            for var in era:

                if _dbg:
                    print('-'*6 + f' {i}: {var}'.ljust(12), end='')

                # calculate if missing
                if not era[var]:
                    if _dbg: print('MISSING'.ljust(9) + '-'*6)
                    era[var] = calc(var, i, eras, _dbg=_dbg)
                    if _dbg: print('\n', pd.DataFrame(eras),'\n')
                    if era[var]: exhausted = False
                else:
                    if _dbg: print('IN'.ljust(9) + '-'*6)

        if _dbg: print(f'..exhausted: {exhausted}')

    gaps = 0
    for row in eras:
        gaps += len([x for x in row if row[x] is None])

    print(f'\nFinished with {gaps} gaps, after {iters} iterations')
    return eras


def calc(var, i, eras, excls=None, _dbg=False):

    if _dbg: print(f'\ncalling calc for {i}, {var}')

    # need to make sure don't loop over Nones, so keep and pass on
    # a list of exclusions, which we know are None
    # Start by appending the current var to that list, so it never 
    # gets calced again, incl in this branch
    if excls is None:
        excls = set()
    excls.add((i, var))

    # first load in the working variables for the inference calculations
    # if not None, write values into working variables
    # if None, and not in excls, calc them
    # if None and in excls, leave as None
    # - also exclude excls

    working_vars = {}

    for v in eras[i]:
        if not eras[i][v] and (i, v) not in excls:
            working_vars[v] = calc(v, i, eras, excls)
        else:
            working_vars[v] = eras[i][v]

    # Pick up a couple of variables from next era, calling calc() if missing
    if i < len(eras) - 1:
        working_vars['next_start'] = eras[i + 1]['start']
        if not working_vars['next_start'] and (i + 1, 'start') not in excls:
            working_vars['next_start'] = calc('start', i + 1, eras, excls)
         
    # And for prev - just pick them up, don't try to calc
    if i > 0:
        working_vars['prev'] = eras[i - 1]
        pprint(working_vars)
    else:
        working_vars['prev'] = {}


    # call the inference calc for the target variable
    # (all the actual work)
    out = calc_f(var, i, working_vars)

    # write to eras
    eras[i][var] = out

    # also return for use in calling calcs
    return out
