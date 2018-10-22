import pandas as pd
import numpy as np
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
def make_tx_stream(scheme, end_per=None):
    """Construct a stream of txs from an input schedule

    Input scheme is a list of dicts, each of which describes
    an 'era' of transaction flows.

    Dict keys:
        - 'start': the start month of the era
        - 'end': the last month of the era
        - 'periods': the number of months in the era
        - 'gr': growth rate per period, default = 0

    Required inputs:
        - the initial era must have a 'start'
        - otherwise each era's duration must be inferrable from some
          combination of (in order of precedence):
              - it's own 'periods'
              - it's own 'end'
              - the 'start's of the adjacent eras

    Will terminate when it finds an era of zero duration
    """

    starts = []
    durations = []
    g_rates = []

    if not 'start' in scheme[0]:
        print("Need an initial start month")
        return 1

    starts.append(scheme[0]['start'])

    if 'periods' in scheme[0]:
        durations.append(scheme[0]['periods'])

    elif 'end' in scheme[0]:
        durations.append(scheme[0]['end'] - scheme[0]['start'])

    else:
        print("Need an initial periods or end month")
        return 1

    g_rates.append(scheme[0].get('gr', 0))

    print(f'Initialised: start {starts[0]}, duration {durations[0]}\n')

    # get start month, duration and growth for each era after start
    i = 1 # enumerate, starting from row 1, not 0
    for era in scheme[1:]:
        print(f'Chronology for era {i}..', end=' ')
        # always create a start and duration for each era
        # so can always get the start from previous

        if 'start' in era:
            start = era['start']
        else:
            start = (starts[-1] + durations[-1])

        if 'periods' in era:
            print(' - using own periods')
            duration = era['periods']

        elif 'end' in era:
            print(' - using end of own era')
            duration = era['end'] - start

        elif 'start' in scheme[i+1]:
            print(' - looking forward')
            duration = scheme[i+1]['start'] - start

        else:
            # terminal
            print(' - no duration, so terminating')
            duration = 0

        print(f'..starts {start}, duration {duration}\n')
        starts.append(start)
        durations.append(duration)
        g_rates.append(era.get('gr', 0))

        # terminate if reqd
        if duration == 0:
            # notify if termination apparently premature
            if i < len(scheme): 
                print(f'Terminating after {i + 1} eras of {len(scheme)}')
            break
        i += 1

    print(starts)
    print(durations)
    # now construct the amounts

def make_eras(era_list, end_per=None):
    """Take a list of eras and:
        - for each era generate a series of tx amounts,
          with a Period index
        - concat these and return
    NB there may be discontinuities in index (cd later fill with zero if reqd)

    Issues:
        - inferring amts when blank
        - dealing with termination (actually easy now, do at end)
        - applying frequencies of tx and gr application (don't worry yet)
    """

    eras = []

    for i, era in enumerate(era_list):
        init_amt = None
        last_amt = None

        # this will be handy if amt not in era dict
        if i != 0:
            last_amt = eras[i-1][-1] * (1 + era_list[i-1]['g_rate'])

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
        exps = np.arange(era['periods'])
        arr = init_amt * ((1 + era['g_rate']) ** exps)

        # make index
        # TODO - apply tx_freq
        ind = pd.PeriodIndex(start=era['start'],
                             freq='M',
                             periods=era['periods'])

        eras.append(pd.Series(data=arr, index=ind))

    return pd.concat(eras)


def make_eras_inputs(in_list, end_per=None):
    """Fills out an input list to give full inputs for generating eras.
    Does this by doing all the required inference to complete, for each
    era:
        - start_m
        - periods
        - init_amt
        - g_rate
        (- tx_freq?)
        (- growth_effect_freq?)

    If end_per not None, need to add a terminal period (if last normal period
    has any tx value, and has not been terminated with periods or end)
    """
    # set up out list
    out = []

    # deal here with possibility of an end period, if:
    #   end_per not None and
    #   last real period not explicitly terminated with 'periods' or 'end'
    terminated = set(['periods', 'end']).intersection(in_list[-1].keys())

    if (end_per is not None) and not terminated:
        in_list[-1]['end'] = end_per
        print('adding an end period to last row')

    for i, row in enumerate(in_list):
        print(f'\nEntering row {i}.. ')
        # build up a dict to append to out list
        era_dict = {}

        # 1. start period
        if 'start' in row:
            print(f'.. has its own start')
            era_dict['start'] = row['start']

        # otherwise look back for start, as long as not at row 0
        elif i > 0:
            print(f'.. using previous row to infer start')
            era_dict['start'] = out[-1]['start'] + out[-1]['periods'] + 1

        else:
            print('could not compute a start month for this row, exiting')
            return 1

        # 2. number of periods
        if 'periods' in row:
            print(f'.. has its own periods')
            era_dict['periods'] = row['periods']

        elif 'end' in row:
            print(' - using end supplied')
            era_dict['periods'] = row['end'] - era_dict['start']

        # otherwise look forward, as long as not at last row
        elif i < (len(in_list) - 1) and 'start' in in_list[i+1]:
            print(f'.. using next row to infer periods')
            era_dict['periods'] = in_list[i+1]['start'] - era_dict['start']

        else:
            print('could not compute periods for this row, exiting')
            return 1

        # 3. initial amount - may be None, and infer when building trajectory
        era_dict['amt'] = row.get('amt', None)
        era_dict['g_rate'] = row.get('g_rate', 0)
        era_dict['tx_freq'] = row.get('tx_freq', 1)
        era_dict['g_rate_effect_freq'] = row.get('g_rate_effect_freq', 1)
        era_dict['add'] = row.get('add', 0)
        era_dict['mult'] = row.get('mult', 1)

        out.append(era_dict)

    return out




class tx_stream:
    """Class to hold an income stream, with rules to describe over time
    """
    def __init__(self, amt, start_m, stop_m=None, periods=None, g_rate=0):

        self.start_m = start_m
        self.amt = amt
        self.g_rate = g_rate
        
        if stop_m is None and periods is not None:
            self.stop_m = start_m + periods
            self.periods = periods

        elif periods is None and stop_m is not None:
            self.stop_m = stop_m
            self.periods = stop_m - start_m

        self.amt = amt

    def ser(self):
        data = self.amt * ((1 + self.g_rate) ** np.arange(self.periods))
        ind = pd.PeriodIndex(start=self.start_m,
                             periods=self.periods,
                             freq='M')

        ser = pd.Series(data, index=ind)
        return ser


    def __str__(self):
        out = (f'start_m: {self.start_m},\n'
               f'stop_m: {self.stop_m},\n'
               f'periods: {self.periods},\n'
               f'amt: {self.amt},\n'
             )
        return out

def afunc():
    print('hey')
