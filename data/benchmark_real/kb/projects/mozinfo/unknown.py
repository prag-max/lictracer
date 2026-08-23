class unknown(object):
    """marker class for unknown information"""

    # pylint: disable=W1629
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __str__(self):
        return "UNKNOWN"