#import openerp_proxy.orm.record
import six
import numbers
import collections

__all__ = ('empty_cache', 'Cache', 'ObjectCache')


class ObjectCache(dict):
    """ Cache for object / model data

        Automatically generates empty data dicts for records requested.
        Also contains object context
    """
    __slots__ = ('_root_cache', '_object', '_context')

    def __init__(self, root, obj, *args, **kwargs):
        self._root_cache = root
        self._object = obj
        self._context = kwargs.pop('context', None)
        super(ObjectCache, self).__init__(*args, **kwargs)

    @property
    def context(self):
        """ Return context instance related to this cache
        """
        return self._context

    def __missing__(self, key):
        self[key] = {'id': key}
        return self[key]

    def update_keys(self, keys):
        if not self:
            # for large amounts of data, this may be faster (no need for set
            # and difference calls)
            self.update({cid: {'id': cid} for cid in keys})
        else:
            self.update({cid: {'id': cid} for cid in set(keys).difference(six.viewkeys(self))})
        return self

    def update_context(self, new_context):
        """ Updates or sets new context for thes ObjectCache instance

            :param dict new_context: context dictionary to update cached context with
            :return: updated context
        """
        if new_context is not None:
            if self.context is None:
                self.context = new_context
            else:
                self.context.update(new_context)
        return self.context

    def get_ids_to_read(self, field):
        """ Return list of ids, that have no specified field in cache
        """
        return [key for key, val in six.viewitems(self) if field not in val]

    def cache_field(self, rid, ftype, field_name, value):
        """ This method impelment additional caching functionality,
            like caching related fields, and so...

            :param int rid: Record ID
            :param str ftype: field type
            :param str field_name: name of field
            :param value: value to cache for field
        """
        self[rid][field_name] = value
        if value and ftype == 'many2one':
            rcache = self._root_cache[self._object.columns_info[field_name]['relation']]

            if isinstance(value, numbers.Integral):
                rcache[value]  # internal dict {'id': key} will be created by default (see ObjectCache)
            elif isinstance(value, collections.Iterable):
                rcache[value[0]]['__name_get_result'] = value[1]
        elif value and ftype in ('many2many', 'one2many'):
            rcache = self._root_cache[self._object.columns_info[field_name]['relation']]
            rcache.update_keys(value)

    def parse_prefetch_fields(self, fields):
        """ Parse fields to be prefetched, sparating, cache's object fields
            and related fields.

            Used internaly

            :param list fields: list of fields to prefetch
            :return: tuple(prefetch_fields, related_fields),
                     where prefetch_fields is list of fields, to be read for
                     current object, and related_fields is dictionary of form
                     ``{'related.object': ['relatedfield1', 'relatedfield2.relatedfield']}``
        """
        rel_fields = collections.defaultdict(list)
        prefetch_fields = []
        for field in fields:
            field_path = field.split('.', 1)
            xfield = field_path.pop(0)
            prefetch_fields.append(xfield)
            relation = self._object.columns_info.get(xfield, {}).get('relation', False)
            if field_path and relation:
                rel_fields[relation].append(field_path[0])  # only one item left

        return prefetch_fields, rel_fields

    def prefetch_fields(self, fields):
        """ Prefetch specified fields for this cache.
            Also, dot (".") may be used in field name
            to prefetch related fields::

                cache.prefetch_fields(
                    ['myfield1', 'myfields2_ids.relatedfield'])

            :param list fields: list of fields to prefetch

        """
        to_prefetch, related = self.parse_prefetch_fields(fields)

        col_info = self._object.columns_info
        for data in self._object.read(list(self), to_prefetch):
            for field, value in data.items():

                # Fill related cache
                ftype = col_info.get(field, {}).get('type', None)
                self.cache_field(data['id'], ftype, field, value)

        if related:
            # TODO: think how to avoid infinite recursion and double reads
            for obj_name, rfields in related.items():
                self._root_cache[obj_name].prefetch_fields(rfields)


class Cache(dict):
    """ Cache to be used for Record's data
    """
    __slots__ = ('_proxy',)

    def __init__(self, proxy, *args, **kwargs):
        self._proxy = proxy
        super(Cache, self).__init__(*args, **kwargs)

    @property
    def proxy(self):
        """ Access to Client instance this cache is belongs to
        """
        return self._proxy

    def __missing__(self, key):
        try:
            obj = self._proxy.get_obj(key)
        except ValueError:
            raise KeyError("There is no object with such name: %s" % key)
        self[key] = ObjectCache(self, obj)
        return self[key]


def empty_cache(client):
    """ Create instance of empty cache for Record

        :param Client client: instance of Client to create cache for
        :return: instance of Cache class
        :rtype: Cache

        Cache is dictionary-like object with structure like::

            cache = {
                'product.product': {
                    1: {
                        'id': 1,
                        'name': 'product1',
                        'default_code': 'product1',
                    },
                },
            }

    """
    return Cache(client)

