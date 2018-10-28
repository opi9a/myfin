from no_Nones import no_Nones

def get_end(working_vars, i, _dbg=True):

    var = 'end'

    last = working_vars['last']
    repeats = working_vars['repeats']
    freq = working_vars['freq']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    next_start = working_vars['prev'].get('start', None)

    if no_Nones([start, freq, repeats]):
        out = start + (freq * repeats) + freq - 1
        if _dbg: print(f'*** [1] writing {out} to {var} in row {i} *** ')
        return out

    if no_Nones([next_start]):
        out = next_start - 1
        if _dbg: print(f'*** [2] writing {out} to {var} in row {i} *** ')
        return out

    if no_Nones([last, freq]):
        out = last + freq - 1
        if _dbg: print(f'*** writing {out} to {var} in row {i} *** ')
        return out

    return None

