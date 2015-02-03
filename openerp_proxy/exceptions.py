class Error(Exception):
    """ Base class for exceptions"""
    pass


class ConnectorError(Error):
    """ Base class for exceptions related to connectors """
    pass


class ObjectException(Error):
    """ Base class for exceptions related to Objects """
    pass
