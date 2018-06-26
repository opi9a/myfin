import pandas as pd

class Account():

    """Main class for accounting objects

    Attributes:

        unit            : eg 'gbp', 'btc'
                          (default is 'goods' for non financials)

        classification  : a hierarchy of categories above the object.
                          eg if object is fuel: 'consumption/travel'

        view            : all transactions labelled with object's name
                          - a view of the tx_df
                        TODO, options eg all or in / out only

    Methods:

        sum             : return sum of transactions
                            - optional date since
                            - optional from or to only

        time_course     : return daily balance over a period
                            - or could do incidence of transactions / spend

        __add__         : two Account instances added (with '+') are to 
                          return a new instance with the aggregated view, of
                          the underlying tx_df.
                          (work out later how to deal with other stuff like
                          any future growth rates etc)
todo

- ensure tx_df is sorted by date always

- implement addition method to classes to return pd.concat or whatever
   (keep as views)

- support smart aggregation, so base accounts can be attributed to multiple
   higher level categories, but overlap is dealt with when aggregating

- support prod and cons account extrapolation, using eg manual rules or 
   automatic based on detected trends

- projection based on assets: metaclasses of accounts
    eg Crypto, Property. Can have separate ones eg pensions.
    Net consumption comes out of..

- store a parsing function in accounts for loading transactions from standard
    statement structure / format
    """

    def __init__(self, name, tx_df, input_type, col_mapper,
                 unit=None, classification=None):

        self.name = name
        self.classification = classification
        self.tx_df = tx_df

        if input_type not in ['credit_debit', 'net_amt', 'to_from']:

            print("""Need input_type to be one of:
                  'credit_debit', 'net_amt', 'to_from'""")

            self.input_type = None
            self.col_mapper = None

        else:
            self.input_type = input_type 
            self.col_mapper = col_mapper

        if unit == None:
            self.unit = 'goods'

        # set up some boolean filters for the account
        # - separate in and out transactions
        self._outs = (self.tx_df['from'] == self.name)
        self._ins = (self.tx_df['to'] == self.name)


    def view(self, start_date=None, end_date=None):
        """TODO
        """
        date_slice = slice(start_date, end_date, None)

        return (self.tx_df.loc[self._outs | self._ins]
                          .loc[date_slice])


    def __repr__(self):
        return self.name
