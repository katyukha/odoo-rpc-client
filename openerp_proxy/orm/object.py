#import openerp_proxy.orm.record as Record

__all__ = ('get_object_class', 'ObjectBase')


class ObjectType(type):
    """ Metaclass for all objects
    """

    _object_base_classes = []

    __generated_object_class = None

    def __new__(mcs, name, bases, attrs):
        inst = super(ObjectType, mcs).__new__(mcs, name, bases, attrs)
        if getattr(inst, '_generated', False):
            return inst

        if inst not in mcs._object_base_classes:
            mcs._object_base_classes.insert(0, inst)
            mcs.__generated_object_class = None  # Clean cache

        return inst

    @classmethod
    def get_object_class(mcs):
        """ Returns class to be used to build Object instance.
        """
        if mcs.__generated_object_class is None:
            obj_cls = type("Object", tuple(mcs._object_base_classes), {'_generated': True})
            mcs.__generated_object_class = obj_cls
        return mcs.__generated_object_class


def get_object_class():
    """ Return object class
    """
    return ObjectType.get_object_class()


# TODO: think about connecting it to service instead of Proxy
class ObjectBase(object):
    """ Base class for all Objects

        Provides simple interface to remote osv.osv objects

            erp = ERP_Proxy(...)
            sale_obj = ObjectBase(erp, 'sale.order')
            sale_obj.search([('state','not in',['done','cancel'])])
    """
    __metaclass__ = ObjectType

    def __init__(self, erp_proxy, object_name):
        self._erp_proxy = erp_proxy
        self._obj_name = object_name

        self._columns_info = None

    @property
    def name(self):
        """ Name of the object
        """
        return self._obj_name

    @property
    def proxy(self):
        """ ERP_Proxy instance, this object is relatedto
        """
        return self._erp_proxy

    # Overeiddent to add some standard method to be available in introspection
    # Useful for IPython auto completition
    def __dir__(self):
        res = dir(super(ObjectBase, self))
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    def __getattribute__(self, name):
        # TODO: remove erp_proxy arg. use self.proxy instead
        # Or better relate it to object service instead
        def MethodWrapper(erp_proxy, object_name, method_name):
            """ Wraper around ERP objects's methods.

                for internal use.
                It is used in ERP_Object class.
            """
            def wrapper(*args, **kwargs):
                return erp_proxy.execute(object_name, method_name, *args, **kwargs)
            return wrapper

        res = None
        try:
            res = super(ObjectBase, self).__getattribute__(name)
        except AttributeError:
            res = MethodWrapper(self.proxy, self.name, name)

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
            fields_obj = self.proxy.get_obj('ir.model.fields')
            fields = fields_obj.search_records([('model', '=', self.name)])
            for field in fields:
                columns_info[field.name] = field

            self._columns_info = columns_info

        return self._columns_info
