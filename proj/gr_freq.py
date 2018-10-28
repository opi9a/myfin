from no_Nones import no_Nones

def get_gr_freq(working_vars, i, _dbg=False):
    """
    """

    var = 'gr_freq'

    last = working_vars['last']
    repeats = working_vars['repeats']
    freq = working_vars['freq']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    next_start = working_vars['prev'].get('start', None)

    # if no_Nones([start, freq, repeats]):
    #     out = start + (freq * repeats) + freq - 1
    #     if _dbg: print(f'*** writing {out} to {var} in row {i} *** ')
    #     return out

    return None

