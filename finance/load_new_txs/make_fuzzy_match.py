# myfin/finance/load_new_txs/make_fuzzy_match.py
"""
Single function to return a fuzzy match for a given input string
and reference set.
"""

from fuzzywuzzy import fuzz, process


def make_fuzzy_match(input_string, reference_set, threshold=55):
    """
    Single function to return a fuzzy match for a given input string
    and reference set.
    """

    matches = {}

    scorers = {'ratio': fuzz.ratio,
               # 'partial_ratio': fuzz.partial_ratio,
               'token_set_ratio': fuzz.token_set_ratio,
               'token_sort_ratio': fuzz.token_sort_ratio,
              }

    for scorer in scorers:
        matches[scorer] = process.extractOne(input_string, reference_set,
                                             scorer=scorers[scorer])

    top_hit = max(matches, key=lambda x: matches[x][1])

    if matches[top_hit][1] >= threshold:
        return matches[top_hit][0]

    return None
