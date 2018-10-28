
def no_Nones(reqd):
    """Returns True of there are no None values in reqd
    """
    return all([x is not None for x in reqd])
