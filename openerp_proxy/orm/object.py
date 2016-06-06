import six
from extend_me import ExtensibleByHashType

from ..utils import (AttrDict,
                     DirMixIn,
                     preprocess_args,
                     stdcall)


__all__ = ('Object', 'get_object')


ObjectType = ExtensibleByHashType._('Object', hashattr='name')


def get_object(client, name):
    """ Create new Object instance.

        :param client: Client instance to bind this object to
        :type client: Client
        :param name: name of object. Ex. 'sale.order'
        :type name: str
        :return: Created Object instance
        :rtype: Object
    """
    cls = ObjectType.get_class(name, default=True)
    return cls(client, name)


# TODO: implement clean caches new columns may be defined, when new addon was
# installed
@six.python_2_unicode_compatible
class Object(six.with_metaclass(ObjectType, DirMixIn)):
    """ Base class for all Objects

        Provides simple interface to remote osv.osv objects::

            erp = Client(...)
            sale_obj = Object(erp, 'sale.order')
            sale_obj.search([('state','not in',['done','cancel'])])

        To create new instance - use *get_object* function, it implements
        all extensions magic, whic is highly used in this project

        It is posible to create extension only to specific object.
        Example could be found in ``plugins/module_utils.py`` file.

    """

    __slots__ = ('_service', '_obj_name', '_columns_info')

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
    def client(self):
        """ Client instance, this object is relatedto
        """
        return self.service.client

    def __getattr__(self, name):
        def method_wrapper(object_name, method_name):
            """ Wraper around Odoo objects's methods.

                for internal use.
                It is used in Object class.
            """
            @stdcall
            def wrapper(*args, **kwargs):
                return self.service.execute(object_name,
                                            method_name,
                                            *args,
                                            **kwargs)
            name = str('%s:%s' % (object_name, method_name))
            wrapper.__name__ = name
            return wrapper

        # Private methods are not available to be called via RPC
        if name.startswith('_'):
            raise AttributeError("Private methods are not exposed to RPC. "
                                 "(attr: %s)" % name)

        setattr(self, name,  method_wrapper(self.name, name))
        return getattr(self, name)

    def __str__(self):
        return u"Object ('%s')" % self.name

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        assert isinstance(other, Object), \
            "Comparable only with instances of Object class"
        return self.name == other.name and self.client == other.client

    def _get_columns_info(self):
        """ Calculates columns info
        """
        return AttrDict(self.fields_get())

    @property
    def columns_info(self):
        """ Reads information about fields available on model
        """
        if self._columns_info is None:
            self._columns_info = self._get_columns_info()

        return self._columns_info

    def resolve_field_path(self, field):
        """ Resolves dot-separated field path
            to list of tuples (model, field_name, related_model)

            :param str field: dot-separated field path to resolve

            For example::

                sale_obj = client['sale.order']
                sale_obj.resolve_field_path('partner_id.country_id.name')

            will be resoved to::

                [('sale.order', 'partner_id', 'res.partner'),
                 ('res.partner', 'country_id', 'res.country'),
                 ('res.country', 'name', False)]

        """
        field_path = field.split('.')
        res = []

        model = self.name
        cinfo = self.client[model].columns_info
        f = field_path.pop(0)
        res.append((model, f, cinfo[f].get('relation', False)))

        while field_path:
            model = cinfo[f]['relation']
            cinfo = self.client[model].columns_info
            f = field_path.pop(0)
            res.append((model, f, cinfo[f].get('relation', False)))
        return res

    @property
    def stdcall_methods(self):
        """ Property that returns all methods of this object,
            that supports standard call

            :return: list with names of *stdcall* methods
            :rtype: list(str)
        """
        return [n for n in dir(self)
                if not n.startswith('_') and
                n != 'stdcall_methods' and
                getattr(getattr(self, n, None), '__x_stdcall__', False)]

    @stdcall
    def read(self, ids, fields=None, context=None):
        """ Read *fields* for records with id in *ids*

            Also look at `Odoo documentation
            <https://www.odoo.com/documentation/9.0/reference/orm.html#openerp.models.Model.read>`__
            for this method

            :param int|list ids: ID or list of IDs of records to read data for
            :param list fields: list of field names to read.
                                if not passed all fields will be read.
            :param dict context: dictionary with extra context
            :return: list of dictionaries with data had been read
            :rtype: list
        """
        args, kwargs = preprocess_args(ids, fields, context=context)
        return self.service.execute(self.name, 'read', *args, **kwargs)

    @stdcall
    def write(self, ids, vals, context=None):
        """ Write data in *vals* dictionary to records with ID in *ids*

            For more info, look at `odoo documentation <https://www.odoo.com/documentation/9.0/reference/orm.html#openerp.models.Model.write>`__
            for this method

            :param int|list ids: ID or list of IDs of records to write data for
            :param dict vals: dictinary with values to be written to database
                              for records specified by ids
            :param dict context: context dictionary
        """  # noqa
        args, kwargs = preprocess_args(ids, vals, context=context)
        return self.service.execute(self.name, 'write', *args, **kwargs)

    def create(self, vals, context=None):
        """ Create new record with *vals*

            Also look at `Odoo documentation <https://www.odoo.com/documentation/9.0/reference/orm.html#openerp.models.Model.create>`__
            for this method

            :param dict vals: dictionary with values to be written
                              to newly created record
            :param dict context: context dictionary
            :return: ID of newly created record
            :rtype: int
        """  # noqa
        args, kwargs = preprocess_args(vals, context=context)
        return self.service.execute(self.name, 'create', *args, **kwargs)

    @stdcall
    def unlink(self, ids, context=None):
        """ Unlink records specified by *ids*

            Also look at `Odoo documentation <https://www.odoo.com/documentation/9.0/reference/orm.html#openerp.models.Model.unlink>`__
            for this method

            :param list ids: list of IDs of records to be deleted
        """  # noqa
        args, kwargs = preprocess_args(ids, context=context)
        return self.service.execute(self.name, 'unlink', *args, **kwargs)

    def search(self, *args, **kwargs):
        """search(args[, offset=0][, limit=None][, order=None][, count=False][, context=None])

            Search records by criteria.

            Also look at `Odoo documentation <https://www.odoo.com/documentation/9.0/reference/orm.html#openerp.models.Model.search>`__
            for this method
        """  # noqa
        return self.service.execute(self.name, 'search', *args, **kwargs)
