import pandas as pd
import os

from ..finance import *


#--- SET UP TEST VARIABLES ---


# make some items
test_items = ['Newt Cuffs',
              'TEA CHEST',
              'Playboy subs',
              'Newt Ruffs',
              'umbilical chord']

# define the reqd new categories
new_categs = {}

new_categs['normal'] = ['amphibia',
                     'unknown',
                     'unknown',
                     'unknown',
                     'unknown']  

new_categs['fuzzy'] = ['amphibia',
                    'unknown',
                    'unknown',
                    'amphibia',
                    'unknown']  

#--- TEST FUNCTIONS ---

def make_categ_map(path='categs.csv'):

    # first get rid of existing versions of the file
    if os.path.isfile(path): os.remove(path)

    with open(path, 'w') as f:
        f.write('Newt Cuffs,amphibia\n')
        f.write('TEA CHEST,unknown\n')


def _categorise(fuzziness, categs_path='categs.csv'):
        
    # generate the test csv file
    make_categ_map()

    # set fuzzy flag
    fuzzymatch = True if fuzziness == 'fuzzy' else False
    print(fuzzymatch)

    # call the function        
    categs = categorise(test_items, categs_path, fuzzymatch=fuzzymatch)

    print(categs)

    # check expected categories have been returned
    assert(categs == new_categs[fuzziness])

    # check updated category map
    new_categ_map = pd.read_csv(categs_path, header=None)
    assert(list(new_categ_map[0] == test_items))
    assert(list(new_categ_map[1] == new_categs[fuzziness]))

    
def test_categorise_normal():
    _categorise('normal')
    
def test_categorise_fuzzy():
    _categorise('fuzzy')
    

if __name__ == '__main__':
    _categorise('fuzzy')
