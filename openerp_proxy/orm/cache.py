import six
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
        """ Add new IDs to cache.

            :param list keys: list of new IDs to be added to cache
        """
        if not self:
            # for large amounts of data, this may be faster (no need for set
            # and difference calls)
            self.update({cid: {'id': cid} for cid in keys})
        else:
            self.update({cid: {'id': cid}
                         for cid in set(keys).difference(six.viewkeys(self))})
        return self

    def update_context(self, new_context):
        """ Updates or sets new context for thes ObjectCache instance

            :param dict new_context: context dictionary to update cached
                                     context with
            :return: updated context
        """
        if new_context is not None:
            if self.context is None:
                self._context = new_context
            else:
                self._context.update(new_context)
        return self.context

    def get_ids_to_read(self, *fields):
        """ Return list of ids, that have no at least one of specified
            fields in cache

            For example::

                cache.get_ids_to_read('name', 'country_id', 'parent_id')

            This code will traverse all record ids managed by this cache,
            and find those that have no at least one field in cache.
            This is highly useful in prefetching
        """
        return [key for key, val in six.viewitems(self)
                if any(((field not in val) for field in fields))]

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
            rcache = self._root_cache[self._object.
                                      columns_info[field_name]['relation']]

            if isinstance(value, six.integer_types):  # pragma: no cover
                # internal dict {'id': key} will be created by default
                # (see ObjectCache.__missing__)
                rcache[value]
            elif isinstance(value, (list, tuple)):
                # usualy for many2one fields odoo returns tuples like
                # (id, name), where id is ID of remote record, and name
                # is human readable name of record (result of name_get method)
                # so we cache this name for futher usage too
                rcache[value[0]]['__name_get_result'] = value[1]
        elif value and ftype in ('many2many', 'one2many'):
            rcache = self._root_cache[self._object.
                                      columns_info[field_name]['relation']]
            rcache.update_keys(value)

    def parse_prefetch_fields(self, fields):
        """ Parse fields to be prefetched, sparating, cache's object fields
            and related fields.

            Used internaly

            :param list fields: list of fields to prefetch
            :return: tuple(prefetch_fields, related_fields),
                     where prefetch_fields is list of fields, to be read for
                     current object, and related_fields is dictionary of form
                     ``{'related.object': ['relatedfield1',
                                           'relatedfield2.relatedfield']}``
        """
        rel_fields = collections.defaultdict(list)
        prefetch_fields = set()
        for field in fields:
            field_path = field.split('.', 1)
            xfield = field_path.pop(0)
            xfield_info = self._object.columns_info.get(xfield, None)
            if xfield_info is not None:
                prefetch_fields.add(xfield)
                relation = xfield_info.get('relation', False)
                if field_path and relation:
                    # only one item left
                    rel_fields[relation].append(field_path[0])

        return list(prefetch_fields), rel_fields

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
        for data in self._object.read(self.get_ids_to_read(*to_prefetch),
                                      to_prefetch):
            for field, value in data.items():

                # Fill related cache
                ftype = col_info.get(field, {}).get('type', None)
                self.cache_field(data['id'], ftype, field, value)

        if related:
            # TODO: think how to avoid infinite recursion and double reads
            for obj_name, rfields in related.items():
                self._root_cache[obj_name].prefetch_fields(rfields)


class Cache(dict):
    """ Cache to be used for Record's data.

        This is root cache, which manages model local cache

        cache['res.partner'] -> ObjectCache('res.partner')
    """
    __slots__ = ('_client',)

    def __init__(self, client, *args, **kwargs):
        self._client = client
        super(Cache, self).__init__(*args, **kwargs)

    @property
    def client(self):
        """ Access to Client instance this cache belongs to
        """
        return self._client

    def __missing__(self, key):
        try:
            obj = self._client.get_obj(key)
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
