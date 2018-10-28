from no_Nones import no_Nones

def get_last(working_vars, i, _dbg=True):

    var = 'last'

    # last = working_vars['last']
    repeats = working_vars['repeats']
    freq = working_vars['freq']
    end = working_vars['end']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    next_start = working_vars['prev'].get('start', None)


    reqd = [start, freq, repeats]
    if no_Nones(reqd):
        out = start + (freq * repeats)
        if _dbg: print(f'[1] *** writing {out} to {var} in row {i} *** ')
        return out

    reqd = [end, freq]
    if no_Nones(reqd):
        out = end + 1 - freq
        if _dbg: print(f'[2] *** writing {out} to {var} in row {i} *** ')
        return out

    return None
