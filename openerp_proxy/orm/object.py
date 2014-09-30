from extend_me import Extensible

__all__ = ('Object',)


# TODO: think about connecting it to service instead of Proxy
class Object(Extensible):
    """ Base class for all Objects

        Provides simple interface to remote osv.osv objects

            erp = ERP_Proxy(...)
            sale_obj = Object(erp, 'sale.order')
            sale_obj.search([('state','not in',['done','cancel'])])
    """

    def __init__(self, service, object_name):
        self._service = service
        self._obj_name = object_name

        self._columns_info = None

    @property
    def name(self):
        """ Name of the object
        """
        return self._obj_name

    @property
    def service(self):
        """ Object service instance
        """
        return self._service

    @property
    def proxy(self):
        """ ERP_Proxy instance, this object is relatedto
        """
        return self.service.proxy

    # Overeiddent to add some standard method to be available in introspection
    # Useful for IPython auto completition
    def __dir__(self):
        res = dir(super(Object, self))
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    def __getattr__(self, name):
        def method_wrapper(object_name, method_name):
            """ Wraper around ERP objects's methods.

                for internal use.
                It is used in Object class.
            """
            def wrapper(*args, **kwargs):
                return self.service.execute(object_name, method_name, *args, **kwargs)
            wrapper.__name__ = '%s:%s' % (object_name, method_name)
            return wrapper

        # Private methods are not available to be called via RPC
        if name.startswith('_'):
            raise AttributeError("Private methods are not exposed to RPC. (attr: %s)" % name)

        setattr(self, name,  method_wrapper(self.name, name))
        return getattr(self, name)

    def __str__(self):
        return "Object ('%s')" % self.name
    __repr__ = __str__

    @property
    def columns_info(self):
        """ Reads information about fields available on model
        """
        if self._columns_info is None:
            self._columns_info = self.fields_get()

        return self._columns_info
