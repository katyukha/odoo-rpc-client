import functools
from openerp_proxy.orm.object import ObjectBase
from openerp_proxy import meta

__all__ = (
    'RecordBase',
    'RecordRelations',
    'ObjectRecords',
    'RecordListBase',
)


# TODO: Add ability to use name_get to represent records


class RecordBase(meta.Extensible):
    """ Base class for all Records
    """

    def __init__(self, obj, data):
        assert isinstance(obj, ObjectBase), "obj should be ObjectBase"
        assert isinstance(data, dict), "data should be dictionary structure returned by Object.read"
        self._object = obj
        self._data = data

    def __dir__(self):
        res = dir(super(RecordBase, self))
        res.extend(self._data.keys())
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    @property
    def _service(self):
        """ Returns instance of related Object service instance
        """
        return self._object.service

    @property
    def _proxy(self):
        """ Returns instance of related ERP_Proxy object
        """
        return self._object.proxy

    @property
    def _columns_info(self):
        """ Returns dictionary with information about columns of related object
        """
        return self._object.columns_info

    @property
    def as_dict(self):
        """ Provides dictionary with record's data in raw form
        """
        return self._data.copy()

    def __str__(self):
        return "Record (%s, %s)" % (self._object.name, self.id)
    __repr__ = __str__

    # Allow dictionary access to data fields
    def __getitem__(self, name):
        return self._data[name]

    # Allow to access data as attributes and call object's methods
    # directly from record object
    def __getattribute__(self, name):
        res = None
        try:
            res = super(RecordBase, self).__getattribute__(name)
        except AttributeError:
            try:
                res = self[name]   # Try to get data field
            except KeyError:
                method = getattr(self._object, name)
                res = functools.partial(method, [self.id])
        return res

    def refresh(self):
        self._data.update(self._object.read(self.id))
        return self


class RecordRelations(RecordBase):
    """ Adds ability to browse related fields from record

        Allow using '__obj' suffix in field name to retrive Record
        instance of object related via many2one or one2many or many2many
        This means next:

            >>> o = erp_proxy['sale.order.line'].read_records(1)
            >>> o.order_id
            ... [25, 'order_name']
            >>> o.order_id__obj
            ... Record (sale.order, 25)
    """

    def __init__(self, obj, data):
        super(RecordRelations, self).__init__(obj, data)
        self._related_objects = {}

    def _get_many2one_rel_obj(self, name, cached=True):
        """ Method used to fetch related object by name of field that points to it
        """
        if name not in self._related_objects or not cached:
            rel_data = self[name]
            if rel_data:
                rel_id = rel_data[0]  # Do not forged about relations in form [id, name]
                relation = self._columns_info[name].relation
                rel_obj = self._service.get_obj(relation)
                self._related_objects[name] = rel_obj.read_records(rel_id)
            else:
                self._related_objects[name] = False
        return self._related_objects[name]

    def _get_one2many_rel_obj(self, name, cached=True, limit=None):
        """ Method used to fetch related objects by name of field that points to them
            using one2many relation
        """
        if name not in self._related_objects or not cached:
            relation = self._columns_info[name].relation
            rel_obj = self._service.get_obj(relation)
            rel_ids = self[name]   # Take in mind that field value is list of IDS
            self._related_objects[name] = rel_obj.read_records(rel_ids)
        return self._related_objects[name]

    def _get_related_field(self, name):
        """ Method to fetch related object's data
        """
        col_info = self._columns_info[name]
        if col_info.ttype == 'many2one':
            return self._get_many2one_rel_obj(name)
        elif col_info.ttype == 'one2many' or col_info.ttype == 'many2many':
            return self._get_one2many_rel_obj(name)
        else:
            raise KeyError("There are no related field %s in model %s" % (name, self._object.name))

    def __getitem__(self, name):
        # Allow using '__obj' suffix in field name to retrive ERP_Record
        # instance of object related via many2one or one2many or many2many
        # This means next:
        #    >>> o = db['sale.order.line'].read_records(1)
        #    >>> o.order_id
        #    ... [25, 'order_name']
        #    >>> o.order_id__obj
        #    ... ERP_Record of sale.order, 25
        if name.endswith('__obj'):
            fname = name[:-5]  # cut '__obj' suffix
            return self._get_related_field(fname)
        else:
            return super(RecordRelations, self).__getitem__(name)

    def refresh(self):
        super(RecordRelations, self).refresh()

        # Update related objects cache
        self._related_objects = {}
        return self


# TODO: make it lazy
# TODO: add ability to group list by fields returning dict with sublists
class RecordListBase(meta.Extensible):
    """Class to hold list of records with some extra functionality
    """

    def __init__(self, obj, ids=None, fields=None, context=None):
        """
            @param obj: instance of Object to make this list related to
            @param ids: list of IDs of objects to read data from
            @param fields: list of field names to read by default
            @param context: context to be passed automatocally to methods called from this list
        """
        # TODO: add checks to check if fields are real fields in
        # object.columns_info
        self._ids = [] if ids is None else ids
        self._object = obj
        self._fields = fields
        self._context = context

        self._raw_data = None  # Raw data got from object's 'read' method
        self._records = None  # simple list of Records

    @property
    def ids(self):
        """ IDs of records present in this RecordList
        """
        return self._ids

    @property
    def object(self):
        """ Object this record is related to
        """
        return self._object

    @property
    def raw_data(self):
        """ Raw data in format: [{'id': 1}, {'id': 2}, {'id': 3}, ...]
        """
        if self._raw_data is None:
            kwargs = {}
            if self._fields is not None:
                kwargs['fields'] = self._fields
            if self._context is not None:
                kwargs['context'] = self._context

            self._raw_data = self.object.read(self.ids, **kwargs)
        return self._raw_data  # no copy, brcause of data may be too big to copy it every time

    @property
    def records(self):
        """ Returns list (class 'list') of records
        """
        if self._records is None:
            # TODO: think about using iterator here
            self._records = [RecordBase(self.object, data)
                             for data in self.raw_data]
        return self._records

    @property
    def length(self):
        """ Returns length of this record list
        """
        return len(self.ids)

    # Container related methods
    def __getitem__(self, index):
        return self.records[index]

    def __iter__(self):
        return iter(self.records)

    def __len__(self):
        return len(self.records)

    # Overridden to make ability to call methods of object on list of IDs
    # present in this RecordList
    def __getattribute__(self, name):
        res = None
        try:
            res = super(RecordListBase, self).__getattribute__(name)
        except AttributeError:
            method = getattr(self.object, name)
            res = functools.partial(method, self.ids)
        return res

    def __str__(self):
        return "RecordList(%s): length=%s" % (self.object.name, self.length)
    __repr__ = __str__

    def refresh(self):
        self._raw_data = None
        self._records = None
        return self

    def append(self, item):
        assert isinstance(item, RecordBase), "Only Record instances could be added to list"
        self.ids.append(item.id)
        self.records.append(item)
        return self


class ObjectRecords(ObjectBase):
    """ Adds support to use records from Object classes
    """

    def search_records(self, *args, **kwargs):
        """ Return instance or list of instances of ERP_Record class,
            making available to work with data simpler:

                >>> so_obj = db['sale.order']
                >>> data = so_obj.search_records([('date','>=','2013-01-01')])
                >>> for order in data:
                        order.write({'note': 'order date is %s'%order.date})

            Additionally accepts keyword argument 'read_field' which can be used to specify
            list of fields to read
        """

        read_fields = kwargs.pop('read_fields', [])

        if kwargs.get('count', False):
            return self.search(*args, **kwargs)

        res = self.search(*args, **kwargs)
        if not res:
            return RecordListBase(self, [], *args, **kwargs)

        if read_fields:
            return self.read_records(res, read_fields)
        return self.read_records(res)

    def read_records(self, ids, *args, **kwargs):
        """ Return instance or list of instances of ERP_Record class,
            making available to work with data simpler:

                >>> so_obj = db['sale.order']
                >>> data = so_obj.read_records([1,2,3,4,5])
                >>> for order in data:
                        order.write({'note': 'order data is %s'%order.data})
        """
        assert isinstance(ids, (int, long, list, tuple)), "ids must be instance of (int, long, list, tuple)"
        if isinstance(ids, (int, long)):
            return RecordBase(self, self.read(ids, *args, **kwargs))
        if isinstance(ids, (list, tuple)):
            return RecordListBase(self, ids, *args, **kwargs)

