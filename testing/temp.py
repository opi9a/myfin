import pandas as pd

def make_df():
    columns=[
 'date',      'accX', 'accY', 'amt', 'item',     'id','mode']

    lines = [
["13/01/2001",'acc1', 'cat1',  1.00, 'item1 norm', 1, -1],
["13/01/2005",'acc1', 'cat1',  2.00, 'item1 norm', 2,  1],
["13/01/2006",'acc1', 'cat2', -3.00, 'item2 norm', 3, -1],
["13/01/2002",'acc1', 'acc2',  4.00, 'item1 norm', 4,  1],
["13/01/2002",'acc2', 'acc1', -4.00, 'item1 norm', 5,  1],
["13/01/2003",'acc1', 'cat1',  6.00, 'item1 fuzz', 6,  1],
["13/01/2007",'acc1', 'cat2',  7.00, 'item2 norm', 7,  3]
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
