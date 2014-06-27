import collections

__all__ = ('get_service_class', 'ServiceBase')


class ServiceType(type):
    """ Metaclass for all services
    """

    # Dictionary whith list of classes which are used as bases to build service
    # class for one database
    _service_classes = collections.defaultdict(list)
    _service_base_classes = []

    # Dictionary with already generated service classes
    __service_classes = {}

    def __new__(mcs, name, bases, attrs):
        inst = super(ServiceType, mcs).__new__(mcs, name, bases, attrs)
        if getattr(inst, '_generated', False):
            return inst

        if getattr(inst, '_name', False):
            mcs._service_classes[inst._name].insert(0, inst)
        elif getattr(inst, '_base', False) and inst not in mcs._service_base_classes:
            mcs._service_base_classes.insert(0, inst)
        return inst

    @classmethod
    def get_service_class(mcs, name):
        srv_cls = mcs.__service_classes.get(name, None)
        if srv_cls is None:
            bases = mcs._service_classes.get(name, []) + mcs._service_base_classes
            srv_cls = type("Service", tuple(bases), {'_generated': True})
            mcs.__service_classes['name'] = srv_cls
        return srv_cls


def get_service_class(name):
    """ Return connector specified by it's name
    """
    return ServiceType.get_service_class(name)


class ServiceBase(object):
    """ Base class for all connectors
    """
    __metaclass__ = ServiceType

    def __init__(self, service, erp_proxy):
        self._erp_proxy = erp_proxy
        self._service = service


class Service(ServiceBase):
    """ Service class that implements common behavior of all service
    """
    _base = True

    def __getattribute__(self, name):
        try:
            res = super(Service, self).__getattribute__(name)
        except AttributeError:
            res = getattr(self._service, name)
        return res
