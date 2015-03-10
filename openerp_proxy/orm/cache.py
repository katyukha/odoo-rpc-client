#import openerp_proxy.orm.record
__all__ = ('empty_cache')


class ObjectCache(dict):

    def __init__(self, root, obj, *args, **kwargs):
        self._root_cache = root
        self._object = obj
        self.context = kwargs.pop('context', None)
        super(ObjectCache, self).__init__(*args, **kwargs)

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

    def __missing__(self, key):
        self[key] = {'id': key}
        return self[key]


class Cache(dict):
    """ Cache to be used for Record's data
    """
    def __init__(self, proxy, *args, **kwargs):
        self._proxy = proxy
        super(Cache, self).__init__(*args, **kwargs)

    @property
    def poxy(self):
        return self._proxy

    def __missing__(self, key):
        try:
            obj = self._proxy.get_obj(key)
        except ValueError:
            raise KeyError("There is no object with such name: %s" % key)
        self[key] = ObjectCache(self, obj)
        return self[key]


def empty_cache(proxy):
    """ Create instance of empty cache for Record

        Usualy cache will be dictionary structure like::

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
    return Cache(proxy)

