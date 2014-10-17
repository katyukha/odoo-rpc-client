from openerp_proxy.utils import wpartial
from openerp_proxy.orm.object import Object
from extend_me import Extensible

from collections import defaultdict

__all__ = (
    'Record',
    'RecordRelations',
    'ObjectRecords',
    'RecordList',
    'empty_cache',
)


def empty_cache():
    """ Created instance of empty cache for Record
    """
    return defaultdict(lambda: defaultdict(dict))


class Record(Extensible):
    """ Base class for all Records

        Constructor
            :param obj: instance of object this record is related to
            :param data: dictionary with initial data for a record
                         or integer ID of database record to fetch data from
            :param cache: dictionary of structure {object.name: {object_id: data} }
            :type cache: defaultdict(lambda: defaultdict(dict))

        Note to create instance of cache call *empty_cache*
    """

    def __init__(self, obj, data, cache=None):
        assert isinstance(obj, Object), "obj should be Object"

        self._object = obj
        self._cache = empty_cache() if cache is None else cache
        self._lcache = self._cache[obj.name]

        if isinstance(data, (int, long)):
            self._id = data
            self._data = self._lcache[self._id]
            if self._data.get('id', None) != data:
                self._data.clear()
                self._data['id'] = data
        elif isinstance(data, dict):
            self._id = data['id']
            self._data = self._lcache[self._id]
            self._data.update(data)
        else:
            raise ValueError("data should be dictionary structure returned by Object.read or int representing ID of record")

    def __dir__(self):
        res = dir(super(Record, self))
        res.extend(self._columns_info.keys())
        res.extend(['read', 'search', 'write', 'unlink'])
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

    @property
    def id(self):
        """ Record ID
        """
        return self._id

    @property
    def _name(self):
        """ Returns result of name_get for this record
        """
        if self._data.get('__name_get_result', None) is None:
            data = self._object.name_get(self._lcache.keys())
            for _id, name in data:
                self._lcache[_id]['__name_get_result'] = name
        return self._data['__name_get_result']

    def __unicode__(self):
        return u"R(%s, %s)[%s]" % (self._object.name, self.id, self._name)

    def __str__(self):
        return unicode(self).encode('utf-8')
    __repr__ = __str__

    def __int__(self):
        return self._id

    def __hash__(self):
        return hash((self._object.name, self._id))

    def __eq__(self, other):
        if isinstance(other, Record):
            return other._id == self._id

        if isinstance(other, (int, long)):
            return self._id == other

        return False

    def __ne__(self, other):
        if isinstance(other, Record):
            return other._id != self._id

        if isinstance(other, (int, long)):
            return self._id != other

        return True

    def _get_field(self, ftype, name):
        """ Returns value for field 'name' of type 'type'

            Should be overridden by extensions to provide better hadling for diferent field values
        """
        if name not in self._data:
            # TODO: think about reading all simple fields here
            for data in self._object.read(self._lcache.keys(), [name]):
                self._lcache[data['id']].update(data)

        return self._data[name]

    # Allow dictionary access to data fields
    def __getitem__(self, name):
        if name == 'id':
            return self.id

        field = self._columns_info.get(name, None)

        if field is None:
            raise KeyError("No such field %s in object %s, %s" % (name, self._object.name, self.id))

        ftype = field and field['type']
        return self._get_field(ftype, name)

    # Allow to access data as attributes and call object's methods
    # directly from record object
    def __getattr__(self, name):
        try:
            res = self[name]   # Try to get data field
        except KeyError:
            method = getattr(self._object, name)
            res = wpartial(method, [self.id])
            setattr(self, name, res)
        return res

    def refresh(self):
        self._data.update(self._object.read(self.id, self._data.keys()))
        return self


# TODO: make it lazy
# TODO: completly refactor it
class RecordList(Extensible):
    """Class to hold list of records with some extra functionality

        :param obj: instance of Object to make this list related to
        :type obj: Object instance
        :param ids: list of IDs of objects to read data from
        :type ids: list of int
        :param fields: list of field names to read by default  (not used now)
        :type fields: list of strings (not used now)
        :param cache: dictionary of structure {object.name: {object_id: data} }
        :type cache: defaultdict(lambda: defaultdict(dict))
        :param context: context to be passed automatocally to methods called from this list
        :type context: dict

    """

    def __init__(self, obj, ids=None, fields=None, cache=None, context=None):
        """
        """
        # TODO: add checks to check if fields are real fields in
        # object.columns_info
        self._ids = [] if ids is None else ids
        self._object = obj
        self._cache = empty_cache() if cache is None else cache
        self._fields = obj.simple_fields if fields is None else fields
        self._context = context

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
    def records(self):
        """ Returns list (class 'list') of records
        """
        if self._records is None:
            self._records = [Record(self.object, id_, cache=self._cache)
                             for id_ in self.ids]
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
        return self.length

    def __contains__(self, item):
        if isinstance(item, (int, long)):
            return item in self.ids
        if isinstance(item, Record):
            # TODO: think about smth like: item in self.records
            return item.id in self.ids
        return False

    # Overridden to make ability to call methods of object on list of IDs
    # present in this RecordList
    def __getattr__(self, name):
        method = getattr(self.object, name)
        res = wpartial(method, self.ids)
        setattr(self, name, res)
        return res

    def __str__(self):
        return "RecordList(%s): length=%s" % (self.object.name, self.length)
    __repr__ = __str__

    def refresh(self):
        self._records = None
        for id_ in self.ids:
            del self._cache[self.object.name]
        return self

    def append(self, item):
        assert isinstance(item, Record), "Only Record instances could be added to list"
        self.ids.append(item.id)
        self.records.append(item)
        return self

    # remote method overrides
    def search(self, domain, *args, **kwargs):
        """ Performs normal search, but with addins ``('id', 'in', seld.ids)`` in domain

            :returns: list of IDs found
            :rtype: list of integers
        """
        return self.object.search([('id', 'in', self.ids)] + domain, *args, **kwargs)

    def search_records(self, domain, *args, **kwargs):
        """ Performs normal search_records, but with addins ``('id', 'in', seld.ids)`` in domain

            :returns: RecordList of records found
            :rtype: RecordList instance
        """
        return self.object.search_records([('id', 'in', self.ids)] + domain, *args, **kwargs)


class RecordRelations(Record):
    """ Adds ability to browse related fields from record

        Allow using '__obj' suffix in field name to retrive Record
        instance of object related via many2one or one2many or many2many
        This means next:

            >>> o = erp_proxy['sale.order.line'].read_records(1)
            >>> o.order_id
            ... R(sale.order, 25)[SO025]
    """

    def __init__(self, *args, **kwargs):
        super(RecordRelations, self).__init__(*args, **kwargs)
        self._related_objects = {}

    def _get_many2one_rel_obj(self, name, rel_data, cached=True):
        """ Method used to fetch related object by name of field that points to it
        """
        if name not in self._related_objects or not cached:
            relation = self._columns_info[name]['relation']
            # Update related cache with data been read
            for _cdata in self._lcache.values():
                _cval = _cdata.get(name, False)
                if _cval and _cval[0] not in self._cache[relation]:
                    self._cache[relation][_cval[0]].update({
                        'id': _cval[0],
                        '__name_get_result': _cval[1],
                    })
            # End cache related code

            if rel_data:
                rel_id = rel_data[0]  # Do not forged about relations in form [id, name]
                rel_obj = self._service.get_obj(relation)
                self._related_objects[name] = Record(rel_obj, rel_id, cache=self._cache)
            else:
                self._related_objects[name] = False
        return self._related_objects[name]

    def _get_one2many_rel_obj(self, name, rel_ids, cached=True, limit=None):
        """ Method used to fetch related objects by name of field that points to them
            using one2many relation
        """
        if name not in self._related_objects or not cached:
            relation = self._columns_info[name]['relation']
            rel_obj = self._service.get_obj(relation)
            self._related_objects[name] = RecordList(rel_obj, rel_ids, cache=self._cache)
        return self._related_objects[name]

    def _get_field(self, ftype, name):
        res = super(RecordRelations, self)._get_field(ftype, name)
        if ftype == 'many2one':
            return self._get_many2one_rel_obj(name, res)
        if ftype in ('one2many', 'many2many'):
            return self._get_one2many_rel_obj(name, res)
        return res

    def __getitem__(self, name):
        # For backward compatability
        if name.endswith('__obj'):
            name = name[:-5]
        return super(RecordRelations, self).__getitem__(name)

    def refresh(self):
        super(RecordRelations, self).refresh()

        # Update related objects cache
        self._related_objects = {}
        return self


class ObjectRecords(Object):
    """ Adds support to use records from Object classes
    """

    @property
    def simple_fields(self):
        """ List of simple fields which could be fetched fast enough

            This list contains all fields that are not function nor binary

            :type: list of strings
        """
        return [f for f, d in self.columns_info.iteritems()
                if d['type'] != 'binary' and not d.get('function', False)]

    def search_records(self, *args, **kwargs):
        """ Return instance or list of instances of Record class,
            making available to work with data simpler:

                >>> so_obj = db['sale.order']
                >>> data = so_obj.search_records([('date','>=','2013-01-01')])
                >>> for order in data:
                        order.write({'note': 'order date is %s'%order.date})

            Additionally accepts keyword argument 'read_field' which can be used to specify
            list of fields to read
        """

        read_fields = kwargs.pop('read_fields', None)

        if kwargs.get('count', False):
            return self.search(*args, **kwargs)

        res = self.search(*args, **kwargs)
        if not res:
            return RecordList(self, [], read_fields)

        if read_fields:
            return self.read_records(res, read_fields)
        return self.read_records(res)

    def read_records(self, ids, fields=None, *args, **kwargs):
        """ Return instance or list of instances of Record class,
            making available to work with data simpler:

                >>> so_obj = db['sale.order']
                >>> data = so_obj.read_records([1,2,3,4,5])
                >>> for order in data:
                        order.write({'note': 'order data is %s'%order.data})
        """
        assert isinstance(ids, (int, long, list, tuple)), "ids must be instance of (int, long, list, tuple)"

        if fields is None:
            fields = self.simple_fields

        if isinstance(ids, (int, long)):
            return Record(self, self.read(ids, fields, *args, **kwargs))
        if isinstance(ids, (list, tuple)):
            return RecordList(self, ids, fields, *args, **kwargs)

        raise ValueError("Wrong type for ids args")

    def browse(self, *args, **kwargs):
        return self.read_records(*args, **kwargs)

