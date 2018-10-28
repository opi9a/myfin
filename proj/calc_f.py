from start import get_start
from freq import get_freq
from end import get_end
from last import get_last
from repeats import get_repeats
from init_amt import get_init_amt
from gr import get_gr
from gr_freq import get_gr_freq

def calc_f(var, i, working_vars):

    if var == 'start':
        return get_start(working_vars, i) 
    
    if var == 'end':
        return get_end(working_vars, i) 
    
    if var == 'last':
        return get_last(working_vars, i) 
    
    if var == 'freq':
        return get_freq(working_vars, i) 
    
    if var == 'repeats':
        return get_repeats(working_vars, i) 
    
    if var == 'init_amt':
        return get_init_amt(working_vars, i) 
    
    if var == 'gr':
        return get_gr(working_vars, i) 
    
    if var == 'gr_freq':
        return get_gr_freq(working_vars, i) 
    

