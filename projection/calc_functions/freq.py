from no_Nones import no_Nones

def get_freq(working_vars, i, _dbg=False):
    """First see if it can be inferred internally within an era.
    If not, inherit previous freq.
    Default to 1

    end = start + (repeats * freq) + freq - 1
    end = start + ((repeats + 1) * freq) - 1
    freq = (end - start + 1) / (repeats + 1) 

    """

    var = 'freq'

    last = working_vars['last']
    repeats = working_vars['repeats']
    # freq = working_vars['freq']
    end = working_vars['end']
    start = working_vars['start']

    prev_end = working_vars['prev'].get('end', None)
    prev_freq = working_vars['prev'].get('freq', None)
    next_start = working_vars['next_start']


    if no_Nones([start, last, repeats]):
        out = int((last - start) / (repeats - 1))
        if _dbg: print(f'*** [0] writing {out} to {var} in row {i} *** ')
        return out

    if no_Nones([start, end, repeats]):
        out =  int((end + 1 - start) / repeats)
        if _dbg: print(f'*** [1] writing {out} to {var} in row {i} *** ')
        return out

    return 1

