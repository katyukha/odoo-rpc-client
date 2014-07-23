#import openerp_proxy.orm.record as Record
from extend_me import Extensible

__all__ = ('ObjectBase',)


# TODO: think about connecting it to service instead of Proxy
class ObjectBase(Extensible):
    """ Base class for all Objects

        Provides simple interface to remote osv.osv objects

            erp = ERP_Proxy(...)
            sale_obj = ObjectBase(erp, 'sale.order')
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
        res = dir(super(ObjectBase, self))
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    def __getattribute__(self, name):
        def MethodWrapper(object_name, method_name):
            """ Wraper around ERP objects's methods.

                for internal use.
                It is used in ERP_Object class.
            """
            def wrapper(*args, **kwargs):
                return self.service.execute(object_name, method_name, *args, **kwargs)
            return wrapper

        res = None
        try:
            res = super(ObjectBase, self).__getattribute__(name)
        except AttributeError:
            # Private methods are not available to be called via RPC
            if name.startswith('_'):
                raise

            res = MethodWrapper(self.name, name)

        return res

    def __str__(self):
        return "Object ('%s')" % self.name
    __repr__ = __str__

    # NOTE: this method requires orm.record to be imported
    @property
    def columns_info(self):
        """ Reads information about fields available on model
        """
        if self._columns_info is None:
            columns_info = {}
            fields_obj = self.service.get_obj('ir.model.fields')
            fields = fields_obj.search_records([('model', '=', self.name)])
            for field in fields:
                columns_info[field.name] = field

            self._columns_info = columns_info

        return self._columns_info
