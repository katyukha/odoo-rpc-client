
__all__ = ('get_connector', 'get_connector_names', 'ConnectorBase')


class ConnectorType(type):
    """ Metaclass for all connectors
    """

    _connectors = {}

    def __new__(mcs, name, bases, attrs):
        inst = super(ConnectorType, mcs).__new__(mcs, name, bases, attrs)
        if getattr(inst, '_name', False):
            mcs._connectors[inst._name] = inst
        return inst

    @property
    @classmethod
    def connectors(mcs):
        return mcs._connectors.keys()

    @classmethod
    def get_connector(mcs, name):
        return mcs._connectors[name]


def get_connector(name):
    """ Return connector specified by it's name
    """
    return ConnectorType.get_connector(name)


def get_connector_names():
    """ Returns lisnt of connector names registered in system
    """
    return ConnectorType.connectors


class ConnectorBase(object):
    """ Base class for all connectors
    """
    __metaclass__ = ConnectorType

    def __init__(self, host, port, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose

    def get_service(self, name):
        raise NotImplementedError
