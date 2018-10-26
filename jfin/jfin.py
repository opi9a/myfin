import pandas as pd
import numpy as np
from pprint import pprint
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
def make_era_series(in_list, end_per=None):
    """Construct a stream of txs from an input schedule

    Input scheme is a list of dicts, each of which describes
    an 'era' of transaction flows.

    Dict keys:
        - 'start': the start month of the era
        - 'freq'
        - 'repeats': the number of months in the era
        - 'end': the last month of the era
        - 'init_amt'
        - 'g_rate': growth rate per period, default = 0
        - 'growth_effect_freq'


    Only requires a minimal set of these keys - eg can infer start of a period
    from the end of the last.

    For each era, in a loop:
        
    1.  Fills out an input list to give full inputs for generating era_series,
    making all the required inferences etc.

    Append this info to a list of era_dicts, as may be useful for later eras

    2.  Then:
        - generate a series of tx amounts, with a Period index reflecting
          frequency of era
        - convert to monthly frequency for series (nans in gaps)
        - apply growth rate, as np.arange, reflecting gr_freq

    Append to era_series list

    Concat era_series and return
    """

    # PART 1 - make the list of parameters for each era

    # set up out era_series list - will hold list of series
    era_series = []

    # also keep the dicts used along the way
    era_dicts = []

    # deal first with possibility of an end period, if:
    #   end_per not None and
    #   last real period not explicitly terminated with 'repeats' or 'end'
    terminated = set(['repeats', 'end']).intersection(in_list[-1].keys())

    if (end_per is not None) and not terminated:
        in_list[-1]['end'] = end_per
        # print('adding an end period to last row')

    for i, row in enumerate(in_list):
        print(f'\nEntering row {i}.. ')
        # build up a dict to use for generating actual series
        era = {}

        # in each case, record the value in row, or look elsewhere if absent
        # 1. start period
        #   - if not passed, look back (if anywhere to look)
        #   - account for freq of past era

        # will be useful to have a compressed version of previous series, 
        # with nans taken out
        prev_ser = era_series[i-1]
        prev_comp = prev_ser.loc[~prev_ser.isnull()]

        if 'start' in row:
            # print(f'.. has its own start')
            era['start'] = row['start']

        # otherwise look back for start, as long as not at row 0
        # remember to increment last period by correct freq
        elif i > 0:
            print(f'.. using previous row to infer start')
            era['start'] = (prev_ser.index[0] + era_dicts[i-1]['tx_freq'])

        else:
            print('could not compute a start month for this row, exiting')
            return 1

        # 2. number of repeats
        if 'repeats' in row:
            # print(f'.. has its own repeats')
            era['repeats'] = row['repeats']

        elif 'end' in row:
            # print(' - using end supplied')
            era['repeats'] = row['end'] - era['start']

        # otherwise look forward, as long as not at last row
        elif i < (len(in_list) - 1) and 'start' in in_list[i+1]:
            # print(f'.. using next row to infer repeats')
            era['repeats'] = in_list[i+1]['start'] - era['start']

        else:
            print('could not compute repeats for this row, exiting')
            return 1

        # 3. initial amount - may be None, and infer when building trajectory
        # CHANGE ALL THESE SO PICK UP FROM PREV IF ABSENT
        if 'amt' in era:
            era['amt'] = row['amt']
        elif i != 0:
            # prev = era_series[i-1]
            era['amt'] = prev
            era_series[i-1][-1] * (1 + era_series[i-1]['g_rate'])

        era['g_rate'] = row.get('g_rate', 0)
        era['tx_freq'] = row.get('tx_freq', 1)
        era['g_rate_effect_freq'] = row.get('g_rate_effect_freq', 1)
        era['add'] = row.get('add', 0)
        era['mult'] = row.get('mult', 1)

        era_dicts.append(era)
        print(era)
        continue


    # PART 2 - actually build the era series

        init_amt = None
        last_amt = None

        # this will be handy if amt not in era dict
        if i != 0:
            prev = era_series[i-1]
            last_amt = prev.loc[~prev.isnull()]
            era_series[i-1][-1] * (1 + era_series[i-1]['g_rate'])

        # get init_amt
        if era['amt'] is not None:
            init_amt = era['amt']

        # need to not be in the first era if extrapolating from previous
        elif i == 0:
            print('need an initial amount')
            return 1

        # extrapolate from previous
        elif era['mult'] is not None:
            init_amt = last_amt * era['mult']

        elif era['add'] is not None:
            init_amt = last_amt + era['add']

        else:
            init_amt = last_amt

        # make amounts array 
        exps = np.arange(era['repeats'])
        f = era.get('g_rate_effect_freq', 1)
        exps = (exps / f).astype(int) * f
        print(exps)
        arr = init_amt * ((1 + era['g_rate']) ** exps)

        # make index
        freq = str(era.get('tx_freq', 1)) + 'M'
        adj_start = era['start'].asfreq(freq)
        ind = pd.PeriodIndex(start=adj_start,
                             freq=freq,
                             repeats=era['repeats'])

        # output with 'M' freq (NaNs in any gaps)
        era_series.append(pd.Series(data=arr, index=ind).asfreq('M'))

    # return pd.concat(era_series)
    return era_series

def do_calc(in_list):

    # copy over vars in in_list to eras
    eras = []
    vars = ['start', 'freq', 'last', 'repeats', 'end']
    for row in in_list:
        era = {var: row.get(var, None) for var in vars}
        eras.append(era)

    # for each era, calc each missing var
    for i, era in enumerate(eras):
        for var in era:
            if not era[var]:
                era[var] = calc(var, i, eras)
                print('\n', pd.DataFrame(eras))

    return eras


def calc(var, i, eras, excls=None):

    print(f'\ncalling calc for {i}, {var}')

    # need to make sure don't loop over Nones, so keep and pass on
    # a list of exclusions, which we know are None
    # So start by appending the current var to that list, so it never 
    # gets calced again, incl in this branch
    if excls is None:
        excls = set()
    excls.add((i, var))
    print('excls', excls)


    # first load in the working variables for the inference calculations
    # if not None, write values into working variables
    # if None, and not in excls, calc them
    # if None and in excls, leave as None
    # - exclude the var being calculated or will make an infinite loop
    # - also exclude excls

    # get working variables, excl target var
    # good reasons to do this manually: clarity, variables are not
    # consistent, eg those from different eras need diff treatment

    start = None
    end = None
    last = None
    freq = None
    repeats = None
    next_start = None
    prev_end = None

    if var != 'start':
        # load the value from eras
        start = eras[i]['start']
        # if None and not excluded, call calc()
        if not start and (i, 'start') not in excls:
            start = calc('start', i, eras, excls)
            print(f'returning from calc() with start = {start}')
         
    if var != 'end':
        end = eras[i]['end']
        if not end and (i, 'end') not in excls:
            end = calc('end', i, eras, excls)
            print(f'returning from calc() with end = {end}')
         
    if var != 'freq':
        freq = eras[i]['freq']
        if not freq and (i, 'freq') not in excls:
            freq = calc('freq', i, eras, excls)
            print(f'returning from calc() with freq = {freq}')
         
    if var != 'repeats':
        repeats = eras[i]['repeats']
        if not repeats and (i, 'repeats') not in excls:
            repeats = calc('repeats', i, eras, excls)
            print(f'returning from calc() with repeats = {repeats}')
         
    if var != 'last':
        last = eras[i]['last']
        if not last and (i, 'last') not in excls:
            last = calc('last', i, eras, excls)
            print(f'returning from calc() with last = {last}')
         
    # Pick up a couple of variables from next and prev eras
    if i < len(eras) - 1:
        next_start = eras[i + 1]['start']
        if not next_start and (i + 1, 'start') not in excls:
            next_start = calc('start', i + 1, eras, excls)
            print(f'returning from calc() with next_start = {next_start}')
         
    if i > 0:
        prev_end = eras[i - 1]['end']
        if not prev_end and (i - 1, 'end') not in excls:
            prev_end = calc('end', i - 1, eras, excls)
            print(f'returning from calc() with prev_end = {prev_end}')
         
    pad = 20
    print('\n--- Working Variables ---')
    print('start'.ljust(pad), start)
    print('end'.ljust(pad), end)
    print('last'.ljust(pad), last)
    print('freq'.ljust(pad), freq)
    print('repeats'.ljust(pad), repeats)
    print('next_start'.ljust(pad), next_start)
    print('prev_end'.ljust(pad), prev_end, end='\n\n')


    # code for inference calcs for each individual variable

    if var == 'last':

        # calc 1 attempt
        if all([start, freq, repeats]):
            out = start + (freq * repeats)
            print(f'*** writing {out} to {var} in row {i} *** ')
            eras[i][var] = out
            return out

        # if get this far, it can't be inferred
        return None

    if var == 'end':
        if all([start, freq, repeats]):
            out = start + (freq * repeats) + freq - 1
            print(f'*** writing {out} to {var} in row {i} *** ')
            eras[i][var] = out
            return out
        return None

    if var == 'freq':
        if all([start, last, repeats]):
            out = int((last - start) / repeats)
            print(f'*** writing {out} to {var} in row {i} *** ')
            eras[i][var] = out
            return out
        return None

    if var == 'start':
        if all([prev_end]):
            out = prev_end + 1
            print(f'*** writing {out} to {var} in row {i} *** ')
            eras[i][var] = out
            return out
        return None


    #     # use current era

    #     if all([freq, repeats, last]):
    #         print(f'calced {var} in row {i} in row from freq, repeats, last')
    #         return last - (freq * repeats)
            
    #     # can also calc from end, freq, repeats but end will be calced anyway

    #     # TODO - look forward for start in next era
    #     return None

    return None
            


class tx_stream:
    """Class to hold an income stream, with rules to describe over time
    """
    def __init__(self, amt, start_m, stop_m=None, repeats=None, g_rate=0):

        self.start_m = start_m
        self.amt = amt
        self.g_rate = g_rate
        
        if stop_m is None and repeats is not None:
            self.stop_m = start_m + repeats
            self.repeats = repeats

        elif repeats is None and stop_m is not None:
            self.stop_m = stop_m
            self.repeats = stop_m - start_m

        self.amt = amt

    def ser(self):
        data = self.amt * ((1 + self.g_rate) ** np.arange(self.repeats))
        ind = pd.PeriodIndex(start=self.start_m,
                             repeats=self.repeats,
                             freq='M')

        ser = pd.Series(data, index=ind)
        return ser


    def __str__(self):
        out = (f'start_m: {self.start_m},\n'
               f'stop_m: {self.stop_m},\n'
               f'repeats: {self.repeats},\n'
               f'amt: {self.amt},\n'
             )
        return out

def afunc():
    print('hey')
