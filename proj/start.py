from no_Nones import no_Nones

def get_start(working_vars, i, _dbg=True):

    var = 'start'

    last = working_vars['last']
    repeats = working_vars['repeats']
    freq = working_vars['freq']

    prev_end = working_vars['prev'].get('end', None)

    if no_Nones([last, repeats, freq]):
        out = last - (repeats * freq)
        if _dbg: print(f'*** [1] writing {out} to {var} in row {i} *** ')
        return out

    if no_Nones([prev_end]):
        out = prev_end + 1
        if _dbg: print(f'*** [2] writing {out} to {var} in row {i} *** ')
        return out

    return None

