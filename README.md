# myfin

tx database:
    - import txs from csv / pdf whatever
    - main function is load_new_txs()
    - assigns fields to each tx:
        - date
        - accX    : the account FROM which tx is made
        - accY    : the account TO which tx is made
        - net_amt : amount, unsigned (?)
        - ITEM    : description of the item
        - _item   : regularised description
        - id      : unique ID
    - accX will normally be written in, as you know which acc
      the txs are coming from
    - assignment of accY needs lookup functionality:
        - look for item's category in cat_db (using fuzzy search)
        - allow users to assign categories and update cat_db
    - creates a main tx_db of them


proj:
    - for planning / budgeting
    - construct streams of future consumption and income
    - project net assets

~/shared/finance/investment:
    - building and monitoring portfolio of assets
    - worthy.py:
        - cmd line tool
        - updates prices (and holdings)
        - reports value
        - stores history
        - updates input to d3 visualisation
    - d3 visualisation: in d3/
        - view available funds on iweb platform
        - view current portfolio (updated by worthy)
        - model different portfolios / changes
