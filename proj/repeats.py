from no_Nones import no_Nones

def get_repeats(working_vars, i, _dbg=False):

    var = 'repeats'

    last = working_vars['last']
    # repeats = working_vars['repeats']
    freq = working_vars['freq']
    end = working_vars['end']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    next_start = working_vars['prev'].get('start', None)

    if no_Nones([start, last, freq]):
        out = int((last - start) / freq)
        if _dbg: print(f'*** writing {out} to {var} in row {i} *** ')
        return out

    return None

