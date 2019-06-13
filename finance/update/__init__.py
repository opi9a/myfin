# myfin/finance/update/__init__.py

"""
Want rules / selections to be serializable, searchable

class Rule:
    name, optional
    selections # a list of conditions, together making a mask for tx_db
    col_to_change
    new_val

namedtuple Selection:
    column, eg '_item'
    operation, from ['equals', 'not_equals', 'contains', 'not_contains']
    term, eg 'LNK'  # leave case-sensitive, allow searching of 'ITEM'

rules implemented by:
    calculate mask from selections
    get selection of tx_db as separate copy
    change col_to_change to new_val
    add back to tx_db


higher order:
    use a console session to:
        build rules (interactively):
            use minilanguage, eg: accX = 'halifax_cc', _item c 'mcdonalds'; 'fast food'
        save, load, edit existing rules
        implement rules

"""

