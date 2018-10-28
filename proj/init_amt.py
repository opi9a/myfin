from no_Nones import no_Nones

def get_init_amt(working_vars, i, _dbg=False):
    """Determine if continuous with previous period:
        - continuous start months

    If so, then extrapolate from previous, using prev gr

    Otherwise just use last amt
    """

    var = 'init_amt'

    last = working_vars['last']
    # repeats = working_vars['repeats']
    freq = working_vars['freq']
    end = working_vars['end']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    next_start = working_vars['prev'].get('start', None)
    prev_freq = working_vars['prev'].get('freq', None)
    prev_repeats = working_vars['prev'].get('repeats', None)
    prev_init_amt = working_vars['prev'].get('amt', None)
    prev_gr = working_vars['prev'].get('gr', None)

    reqd = [prev_init_amt, prev_gr, prev_freq, prev_repeats, start]
    if no_Nones(reqd):
        last_amt = prev_init_amt * ((1 + prev_gr)
                                        ** (prev_freq * prev_repeats))
        if start == prev_end + 1:
        # extrapolate as a continuation
            out = last_amt * ((1 + prev_gr) ** prev_freq)
        else:
            out = last_amt

        if _dbg: print(f'*** writing {out} to {var} in row {i} *** ')
        return out

    return None

