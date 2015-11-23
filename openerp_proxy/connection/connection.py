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

        :param str host: hostname to connect to
        :param int port: port to connect to
        :param dict extra_args: extra arguments for specific connector.
    """

    def __init__(self, host, port, extra_args=None):
        self.host = host
        self.port = port
        self.extra_args = {} if extra_args is None else extra_args

        self.__services = {}

    def update_extra_args(self, **kwargs):
        """ Update extra args and clean service cache
        """
        self.extra_args.update(kwargs)
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
