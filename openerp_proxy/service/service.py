from extend_me import ExtensibleByHashType

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


ServiceType = ExtensibleByHashType._('Service', hashattr='name')


def get_service_class(name):
    """ Return service class specified by it's name
    """
    return ServiceType.get_class(name, default=True)


class ServiceBase(object):
    """ Base class for all Services
    """
    __metaclass__ = ServiceType

    def __init__(self, service, erp_proxy):
        self._erp_proxy = erp_proxy
        self._service = service

    @property
    def proxy(self):
        """ Related ERP_Proxy instance
        """
        return self._erp_proxy

    def __getattribute__(self, name):
        try:
            res = super(ServiceBase, self).__getattribute__(name)
        except AttributeError:
            res = getattr(self._service, name)
        return res
