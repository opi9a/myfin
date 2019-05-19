from no_Nones import no_Nones

def get_init_amt(working_vars, i, _dbg=False):
    """Determine if continuous with previous period:
        - continuous start months

    If so, then extrapolate from previous, using prev gr. 
    Otherwise just use last amt from previous period.

    If can't determine, then use previous init_amt.

    Apply addition and multiplication (if have been able to get a value).
    """

    var = 'init_amt'

    start = working_vars['start']

    prev_freq = working_vars['prev'].get('freq', None)
    prev_repeats = working_vars['prev'].get('repeats', None)
    prev_init_amt = working_vars['prev'].get('init_amt', None)
    prev_gr = working_vars['prev'].get('gr', None)
    prev_end = working_vars['prev'].get('end', None)

    add = working_vars['add']
    mult = working_vars['mult']

    out = None

    reqd = [prev_init_amt, prev_gr, prev_freq, prev_repeats, prev_end, start]
    if no_Nones(reqd):
        last_amt = prev_init_amt * ((1 + prev_gr)
                                        ** (prev_freq * (prev_repeats - 1)))
        if start == prev_end + 1:
        # extrapolate as a continuation
            out = last_amt * ((1 + prev_gr) ** prev_freq)
        else:
            out = last_amt

        if _dbg: print(f'*** [0] writing {out} to {var} in row {i} *** ')

    elif no_Nones([prev_init_amt]):
        out = prev_init_amt
        if _dbg: print(f'*** [1] writing {out} to {var} in row {i} *** ')

    if out is not None:
        out = (out + add) * mult

    return out
