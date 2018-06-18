import pandas as pd
from fuzzywuzzy import fuzz, process

from finance import *

def tfunc():
    print('called the tfunc')

def categorise(items, categ_map_path='categ_map.csv', 
               new_categ_map_path=None, fuzzymatch=False, fuzzy_threshold=80):
    """Returns categories for an iterable of items, based on a lookup
    in the categ_map csv.

    Tries a fuzzy match if asked.
    
    Assign as 'unknown' if not found, AND add item to categ_map.csv 
    with 'unknown' as value.
    """

    # dict for reading in the category map from csv
    categ_map = {}  

    # list to hold the categories to return, corresponding to items
    categories = [] 

    # new assignments to append to categ_map
    new_assigns = {'new_item':[], 'new_category':[]}

    # read in csv as dict (with lower case keys for matching)
    with open(categ_map_path) as f:
        for line in f:
            a, b = line.split(',')
            categ_map[a.lower()] = b[:-1].lower() 

    for item in items:

        # do the lookup - NB may return 'unknown' value,
        categ = categ_map.get(item.lower(), 'not found')

        # append result to categories for output if present in categ_map
        if categ != 'not found':
            categories.append(categ)

        elif fuzzymatch:
            best_match, score = process.extractOne(item, categ_map.keys(),
                                                   scorer=fuzz.token_set_ratio)

            if score >= fuzzy_threshold:
                categories.append(categ_map[best_match])
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append(categ_map[best_match])
                with open('log.txt', 'a') as f:
                    print(f'Fuzzy-matched {item}, with {best_match}, scoring {score}', file=f)

            else:
                categories.append('unknown')
                new_assigns['new_item'].append(item)
                new_assigns['new_category'].append('unknown')
                with open('log.txt', 'a') as f:
                    print(f'No fuzzy match for {item} (best score {score})', file=f)

        else:
            categories.append('unknown')
            new_assigns['new_item'].append(item)
            new_assigns['new_category'].append('unknown')

    if new_assigns:

        if new_categ_map_path is not None:
            categ_map_path = new_categ_map_path

        # note: appending to csv file
        (pd.Series(new_assigns['new_category'], index=new_assigns['new_item'])
                  .to_csv(categ_map_path, mode='a'))

    return categories

