import collections

__all__ = ('get_service_class', 'ServiceBase', 'ServiceManager')


class ServiceManager(object):
    """ Class to hold services related to specific proxy and to
        automaticaly clean service cached on update of service classes

        Usage:
            services = ServiceManager(erp_proxy)
            services.object  # returns service with name 'object'
            services['common']  # returns service with name 'common'
            services.get_service('report')  # returns service with name 'report'
    """

    __managers = []

    @classmethod
    def clean_caches(cls):
        """ Cleans saved service instances, so on next access new service instances will be generated.
            This usualy happens when new service extension enabled (new class inherited from ServiceBase created)
        """
        for manager in cls.__managers:
            manager.clean_cache()

    def __new__(cls, *args, **kwargs):
        inst = super(ServiceManager, cls).__new__(cls, *args, **kwargs)
        cls.__managers.append(inst)
        return inst

    def __init__(self, erp_proxy):
        self._erp_proxy = erp_proxy
        self.__services = {}

    def get_service(self, name):
        """ Returns instance of service with specified name
        """
        service = self.__services.get(name, None)
        if service is None:
            cls = get_service_class(name)
            srv = self._erp_proxy.connection.get_service(name)
            service = cls(srv, self._erp_proxy)
            self.__services[name] = service
        return service

    def clean_cache(self):
        """ Cleans service cache
        """
        self.__services = {}

    def __getattr__(self, name):
        return self.get_service(name)

    def __getitem__(self, name):
        return self.get_service(name)


class ServiceType(type):
    """ Metaclass for all services
    """

    # Dictionary whith list of classes which are used as bases to build service
    # class for one database
    _service_classes = collections.defaultdict(list)
    _service_base_classes = []

    # Dictionary with already generated service classes
    __generated_service_classes = {}

    def __new__(mcs, name, bases, attrs):
        inst = super(ServiceType, mcs).__new__(mcs, name, bases, attrs)
        if getattr(inst, '_generated', False):
            return inst

        if getattr(inst, '_name', False):
            mcs._service_classes[inst._name].insert(0, inst)
            mcs.__generated_service_classes[inst._name] = None  # Clean cache
        elif getattr(inst, '_base', False) and inst not in mcs._service_base_classes:
            mcs._service_base_classes.insert(0, inst)
            mcs.__generated_service_classes = {}  # Clean cache

        ServiceManager.clean_caches()  # Clean service caches
        return inst

    @classmethod
    def get_service_class(mcs, name):
        """ Returns class to be used to build service instance.
        """
        srv_cls = mcs.__generated_service_classes.get(name, None)
        if srv_cls is None:
            bases = mcs._service_classes.get(name, []) + mcs._service_base_classes
            srv_cls = type("Service", tuple(bases), {'_generated': True})
            mcs.__generated_service_classes[name] = srv_cls
        return srv_cls


def get_service_class(name):
    """ Return service class specified by it's name
    """
    return ServiceType.get_service_class(name)


class ServiceBase(object):
    """ Base class for all Services
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


