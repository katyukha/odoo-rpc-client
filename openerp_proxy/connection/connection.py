import six
from extend_me import ExtensibleByHashType

__all__ = ('get_connector', 'get_connector_names', 'ConnectorBase')

ConnectorType = ExtensibleByHashType._('Connector', hashattr='name')


def get_connector(name):
    """ Return connector specified by it's name
    """
    return ConnectorType.get_class(name)


def get_connector_names():
    """ Returns lisnt of connector names registered in system
    """
    return ConnectorType.get_registered_names()


class ConnectorBase(six.with_metaclass(ConnectorType)):
    """ Base class for all connectors
    """

    def __init__(self, host, port, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.__services = {}

    def _get_service(self, name):  # pragma: no cover
        raise NotImplementedError

    def get_service(self, name):
        """ Returns service for specified *name*

            :param name: name of service
            :return: specified service instance
        """
        service = self.__services.get(name, None)
        if service is None:
            service = self._get_service(name)
            self.__services[name] = service

        return service
