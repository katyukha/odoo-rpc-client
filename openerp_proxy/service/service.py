import six
from extend_me import (ExtensibleByHashType,
                       Extensible)

from ..utils import DirMixIn


__all__ = ('get_service_class', 'ServiceBase', 'ServiceManager')


class ServiceManager(Extensible, DirMixIn):
    """ Class to hold services related to specific proxy and to
        automaticaly clean service cached on update of service classes

        Usage::

            services = ServiceManager(erp_proxy)
            services.list                   # get list of registered services
            services.object                 # returns service with name 'object'
            services['common']              # returns service with name 'common'
            services.get_service('report')  # returns service named 'report'
    """

    __managers = []

    def __new__(cls, *args, **kwargs):
        inst = super(ServiceManager, cls).__new__(cls, *args, **kwargs)
        cls.__managers.append(inst)
        return inst

    def __init__(self, erp_proxy):
        self._erp_proxy = erp_proxy
        self.__services = {}

    def __dir__(self):
        res = set(super(ServiceManager, self).__dir__())
        res.update(self.service_list)
        return list(res)

    @property
    def service_list(self):
        """ Returns list of all registered services
        """
        service_names = set()
        service_names.update(list(self.__services))
        service_names.update(ServiceType.get_registered_names())
        return list(service_names)

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

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError("Service '%s' not found."
                                 "Service names could not be "
                                 "started with '_'.")
        return self.get_service(name)

    def __getitem__(self, name):
        return self.get_service(name)

    def __contains__(self, name):
        return name in self.service_list

    @classmethod
    def clean_caches(cls):
        """ Cleans saved service instances, so on next access new service instances will be generated.
            This usualy happens when new service extension enabled (new class inherited from ServiceBase created)
        """
        for manager in cls.__managers:
            manager.clean_cache()

    def clean_cache(self):
        """ Cleans manager's service cache.
        """
        self.__services = {}

    def clean_service_caches(self):
        """ Clean caches of all services handled by this mananger
            usualy this should be called on module update,
            when list of available objects or reports changed
        """
        for service in self.__services.values():
            service.clean_cache()


ServiceType = ExtensibleByHashType._('Service', hashattr='name')


def get_service_class(name):
    """ Return service class specified by it's name
    """
    return ServiceType.get_class(name, default=True)


class ServiceBase(six.with_metaclass(ServiceType, object)):
    """ Base class for all Services
    """

    def __init__(self, service, erp_proxy):
        self._erp_proxy = erp_proxy
        self._service = service

    @property
    def proxy(self):
        """ Related Client instance
        """
        return self._erp_proxy

    def __getattr__(self, name):
        return getattr(self._service, name)

    def clean_cache(self):
        """ To be implemented by subclasses, if needed
        """
        pass
