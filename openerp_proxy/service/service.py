import six
from extend_me import (ExtensibleByHashType,
                       Extensible)

from ..utils import DirMixIn


__all__ = ('get_service_class', 'ServiceBase', 'ServiceManager')


@six.python_2_unicode_compatible
class ServiceManager(Extensible, DirMixIn):
    """ Class to hold services related to specific client and to
        automaticaly clean service cached on update of service classes

        Usage::

            services = ServiceManager(client)
            services.service_list                   # get list of registered services
            services.object                 # returns service with name 'object'
            services['common']              # returns service with name 'common'
            services.get_service('report')  # returns service named 'report'
    """

    __managers = []

    def __new__(cls, *args, **kwargs):
        inst = super(ServiceManager, cls).__new__(cls, *args, **kwargs)
        cls.__managers.append(inst)
        return inst

    def __init__(self, client):
        self._client = client
        self.__services = {}

    def __dir__(self):
        res = set(super(ServiceManager, self).__dir__())
        res.update(self.service_list)
        return list(res)

    @property
    def client(self):
        """ Client instance this ServiceManager is bounded to
        """
        return self._client

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

            :param name: name of service
            :return: specified service instance
        """
        service = self.__services.get(name, None)
        if service is None:
            cls = get_service_class(name)
            srv = self._client.connection.get_service(name)
            service = cls(srv, self.client, name)
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

    def __str__(self):
        return "<ServiceManager for %s>" % self.client


ServiceType = ExtensibleByHashType._('Service', hashattr='name')


def get_service_class(name):
    """ Return service class specified by it's name
    """
    return ServiceType.get_class(name, default=True)


@six.python_2_unicode_compatible
class ServiceBase(six.with_metaclass(ServiceType, object)):
    """ Base class for all Services

        :param service: instance of original service class.
                        must support folowing syntax
                        ``service.service_method(args)``
                        to call remote methods
        :param client: instance of Client, this service is binded to
    """

    def __init__(self, service, client, name):
        self._client = client
        self._service = service
        self._name = name

    @property
    def client(self):
        """ Related Client instance
        """
        return self._client

    @property
    def name(self):
        """ Service name
        """
        return self._name

    def __getattr__(self, name):
        return getattr(self._service, name)

    def clean_cache(self):
        """ To be implemented by subclasses, if needed
        """
        pass

    def __str__(self):
        return "<Service '%s' of %s>" % (self.name, self.client)
