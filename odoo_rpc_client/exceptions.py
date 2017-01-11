class Error(Exception):
    """ Base class for exceptions"""
    pass


class ConnectorError(Error):
    """ Base class for exceptions related to connectors """
    pass


class ClientException(Error):
    """ Base class for client related exceptions
    """
    pass


class ReportError(Error):
    """ Error raise in process of report generation
    """
    pass


class LoginException(ClientException):
    """ This exception should be raised, when operations requires
        login and password. For example interaction with Odoo object service.
    """
    pass


class ObjectException(ClientException):
    """ Base class for exceptions related to Objects """
    pass
