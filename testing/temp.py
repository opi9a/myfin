import pandas as pd


def make_df():
    columns=[
 'date',      'accX', 'accY', 'amt', 'item',     'id','mode']

    lines = [
# first what will be the initial txdb, to which others will add, but also
# will serve as the initial category map to look others up.
# So want to establish an initial item->category mapping that can 
# then also be used to test fuzzy mapping, with a slightly different item.
["13/01/2001",'acc1', 'cat1',  1.00, 'item1 norm',  1, -1],# initial txdb

# Simple new tx, looks up cat1 mapping directly 
["13/01/2005",'acc1', 'cat1',  2.00, 'item1 norm',  2,  1],# 

# A negative flow
["13/01/2006",'acc1', 'cat2', -3.00, 'map to cat2', 3, -1],#   

# A doublet of transactions
["13/01/2002",'acc1', 'acc2',  4.00, 'item1 norm',  4,  1],#   
["13/01/2002",'acc2', 'acc1', -4.00, 'item1 norm',  5,  1],#   

# A fuzzy lookup for cat1
["13/01/2003",'acc1', 'cat1',  6.00, 'item1 fuzz',  6,  1],#   
["13/01/2007",'acc1', 'cat2',  7.00, 'map to cat2', 7,  3],#   
    ] 

    return pd.DataFrame(data=lines, columns=columns).set_index('date')
#    
#    df = pd.DataFrame(columns=['date', 'from', 'to', 'amt', 'item', 'item_from_to', 'uid'])
#    df.loc[0] = [pd.datetime(2009, 1, 3), 'acc 1', 'init_acc', 11.11, 'init_item', 'to', 0]
#
#    df = df.set_index('date')
#
#
#    df['uid'] = df['uid'].astype(int)
#
