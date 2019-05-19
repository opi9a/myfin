import pandas as pd
import numpy as np
from pprint import pprint

from calc_functions import *

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

# temp inputs etc
all_duration = 100
interest_rate = 0.05/12
events = {}
events['all_start'] = pd.Period('1-2019')
events['born'] = pd.Period('1-1987')
events['all_end'] = events['born'] + (all_duration * 12)
events['retire_age'] = 66
events['retire'] = events['born'] + (events['retire_age'] * 12)
events['buy_house'] = pd.Period('1-2022')
house_price = 220000
rent = 800
house_deprec = 0.05



# main variables, which are going to need inferring
vars = ['start', 'freq', 'last', 'repeats', 'end',
       'init_amt', 'gr', 'gr_freq']

# modifier variables won't need inferring, just set defaults here
modifier_defaults = {'add': 0, 'mult': 1}


def make_eras(in_list, _dbg=False):
    """For an input in_list of era dictionaries, return a version
    completed by inference where possible.

    Eg if start, frequency and repeats is known for a particular era,
    the end and last periods will be calculated and inserted.
    """

    # begin by copying over vars in in_list to eras
    eras = []

    # now populate eras, setting modifier defaults as appropriate
    for row in in_list:

        era = {var: row.get(var, None) for var in vars}

        for m in modifier_defaults:
            era[m] = row.get(m, modifier_defaults[m])

        eras.append(era)

    # for each era, calc each missing var
    # - need to keep repeating until changes exhausted
    iters = 0; exhausted = False

    while not exhausted:
        if _dbg: print(f'\nIn iter {iters}..')
        iters += 1; exhausted = True

        for i, era in enumerate(eras):
            # note, not including modifiers
            for var in vars:

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

    print(f'Finished with {gaps} gaps, after {iters} iterations\n')
    return eras


def calc(var, i, eras, excls=None, _dbg=False):
    """Return the value of a variable var, either by simply looking it up
    if it already exists in the eras list or, if not, by attempting to 
    calculate it from the other values in eras.

    var    : the variable to calculate
    eras   : list of eras (in construction)
    i      : the current era (row number in eras list)
    excls  : set of (i, var) tuples already visited on this path

    Works by creating a set of working variables - which are either looked up,
    or generated with a recursive call to calc().  The recursive call also leads
    to additional values for variables being generated, and added to the eras list.

    The working variables are then passed to calc_f(), which directs to the
    function for calculating the particular variable in question.

    To prevent infinite loops excls, a history of variables to exclude, is kept
    and passed at each call of calc().  This includes everything visited 
    already in the course of the current journey (ie in attempting to calculate 
    the initial variable).
    """

    if _dbg: print(f'\ncalling calc for {i}, {var}')

    # initialise history if this is the first iteration
    if excls is None:
        excls = set()
    excls.add((i, var))

    # first load in the working variables for the inference calculations
    # - includes all variables for current era, and previous (not calculated),
    #   plus the start of the next era (which is calculated if missing)
    working_vars = {}

    # variables in the current era
    for v in eras[i]:
        # call calc() if not known (and not excluded)
        if eras[i][v] is None and (i, v) not in excls:
            working_vars[v] = calc(v, i, eras, excls)
        # otherwise just write straight in
        else:
            working_vars[v] = eras[i][v]

    # previous era - just pick them up, don't try to calc
    if i > 0:
        working_vars['prev'] = eras[i - 1]
    else:
        working_vars['prev'] = {}

    # start from next era, calling calc() if missing
    if i < len(eras) - 1:
        working_vars['next_start'] = eras[i + 1]['start']
        if not working_vars['next_start'] and (i + 1, 'start') not in excls:
            working_vars['next_start'] = calc('start', i + 1, eras, excls)

    else:
        working_vars['next_start'] = None
         

    # call the inference calc for the target variable (all the actual work)
    out = calc_f(var, i, working_vars)

    # write to eras
    eras[i][var] = out

    # also return for use in calling calcs
    return out



def calc_f(var, i, working_vars):
    """Passes arguments to the function for calculating each 
    particular variable, and returns the result.
    """

    if var == 'start':
        return get_start(working_vars, i) 
    
    if var == 'end':
        return get_end(working_vars, i) 
    
    if var == 'last':
        return get_last(working_vars, i) 
    
    if var == 'freq':
        return get_freq(working_vars, i) 
    
    if var == 'repeats':
        return get_repeats(working_vars, i) 
    
    if var == 'init_amt':
        return get_init_amt(working_vars, i) 
    
    if var == 'gr':
        return get_gr(working_vars, i) 
    
    if var == 'gr_freq':
        return get_gr_freq(working_vars, i) 


def make_series(in_list, name=None, filled=False):
    """Make a pd series of amounts from a passed list of eras
    """

    if name is None:
        name = 'none' 

    # get completed eras from in_list
    if not filled:
        eras = make_eras(in_list)
    else:
        eras = in_list
    
    out = []

    for era in eras:
        # get index with passed frequency (i.e. may be >1M)
        freq = str(era['freq']) + 'M'
        ind = pd.PeriodIndex(start=era['start'], freq=freq, end=era['last'])

        # make series of init_amt, changing freq
        arr = np.ones(len(ind)) * era['init_amt']
        ser = pd.Series(arr, index=ind, name=name).asfreq('1M')

        # make a series of exponents - 1M only, to allow different gr_freq
        ind2 = pd.PeriodIndex(start=era['start'], freq='1M', end=era['end'])
        exps = (np.arange(len(ind2))/era['gr_freq']).astype(int) * era['gr_freq']
        exps = pd.Series(exps, index=ind2)

        # apply to get final series
        ser = ser * ((1 + era['gr']) ** exps)
        # make exponents, acc to gr_freq
        # apply to series
        
        out.append(ser.loc[~ser.isnull()])

    ser = pd.concat(out)
    ser.name = name
    return ser
