import pandas as pd

def balance_continuum(df):
    """Returns an array with zeroes where balances are consistent with
    net_amounts.

    If balances are consistent, then:
        bal[n]  = bal[n-1] + net_amt[n]
        0 = bal[n] - (bal[n-1] + net_amt[n])
    """
    continuum = (df.balance[1:].values 
            - (df.net_amt[1:].values
              + df.balance[:-1].values))

    continuum[pd.np.abs(continuum) < 10**-3] = 0

    print('bc1')

    return pd.np.concatenate([[0], continuum])



