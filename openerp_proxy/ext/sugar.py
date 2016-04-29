"""
Provides some syntax sugar to ease acces to objects, records, etc

"""

import numbers

from ..utils import DirMixIn
from ..orm.record import (ObjectRecords,
                          get_record_list)
from .. import Client


class ObjectSugar(ObjectRecords):
    """ Provides aditional methods to work with data

        Also defines *__getitem__* and *__call__* methods, to simplify acces
        to records via *ID*, *name_search* and *simple search*. Detailad below.

        Imagine we have Object instance *obj*::

            obj = db.get_obj('stock.move')   # get move obj object
            so_obj = db['sale.order']        # get sale order object

        And this class provides folowing features.

        1. get record by ID::

                move = obj[125]   # returns stock move record with ID=125
                moves = obj[125,126,127]  # returns record list of three move
                                          # records for IDS 125, 126, 127

        2. name_search

           Calling object with record name as first argument will execute name
           search on passed name::

                so = so_obj('SO005')   # Returns sale order with name 'SO005'
                so2 = so_obj('5')      # If there are more than one records
                                       # found by name, then RecordList
                                       # will be returned. In this case
                                       # this call may return list which will
                                       # contain for example sale orders with
                                       # names like 'SO005', 'SO015', etc.

        3. simple search.

           If pass domain as first argument when calling object,
           then *search_records* method will be called with all
           arguments forwarded::

               res = so_obj([('state','=','done')], limit=10)
               # res -> RecordList('sale.order', length=10)

           Also for simple searches without joins it is posible to pass
           just only keyword arguments which all will be converted to domain::

               res = so_obj(state='done')

            But note, that in last way, **all keyword arguments
            will be converted to domain, no one of them will be forwarded
            to search_records**, so it is not posible, for example, to limit
            results at this moment
    """

    def search_record(self, *args, **kwargs):
        """ Aliase to *search_records* method to fetch only one record
            (aditionaly adds *limit=1* keyword argument
        """
        kwargs['limit'] = 1
        return self.search_records(*args, **kwargs)[0]

    # Overriden to be able to read items using index operation
    def __getitem__(self, name):
        if isinstance(name, (numbers.Integral, list, tuple)):
            return self.read_records(name)
        raise KeyError("Bad key: %s! "
                       "Only integer or list of intergers allowed" % name)

    # Overridden to count all records in this object
    def __len__(self):
        return self.search([], count=True)

    # Smart search and name search
    def __call__(self, *args, **kwargs):
        """ Performs name_search by specified 'name'

            (below under name 'name' i mean first of 'args')
            if name is list or tuple, then search_records will be called
            if name not passed or name is None, then kwargs will be used
            to build search domain and search_records will be called
            else name_search method will be used
        """
        args = list(args)
        name = args.pop(0) if args else None

        # no arguments, only keyword arguments passsed,
        # so build domain based on keyword arguments
        if name is None:
            domain = [(k, '=', v) for k, v in kwargs.items()]
            return self.search_records(domain, *args)

        # normal domain passed, then just forward all arguments and
        # keyword arguments to *search_records* method
        if isinstance(name, (list, tuple)):
            return self.search_records(name, *args, **kwargs)

        # implement name_search capability
        context = kwargs.get('context', None)
        res = self.name_search(name, *args, **kwargs)
        ids = [i[0] for i in res]
        if len(ids) == 1:
            return self.read_records(ids[0], context=context)
        return get_record_list(self, ids=ids, context=context)


class ClientSugar(Client, DirMixIn):
    """ Provides some syntax sugar for Client class

        As one of it's features is ability to access objects as
        attributes via *object aliases*. Each aliase is object name
        with underscores replaced by double underscores and dots replaced by
        single underscores and prefixed by underscore.

        For example all folowing lines will return same result

        .. code:: python

            sm = client._stock_move
            sm = client['stock.move']
            sm = client.get_obj('stock.move')

        One more features of this extension class, is ability
        to access plugins directly from client as it's attributes.
        So folowing lines are equal

        .. code:: python

            test_plugin = client.plugins.Test
            test_plugin = client.Test
    """

    def __init__(self, *args, **kwargs):
        super(ClientSugar, self).__init__(*args, **kwargs)
        self._object_aliases = None

    @property
    def object_aliases(self):
        """ Property, that holds list of all object aliases
            for this Client instance
        """
        if self._object_aliases is None:
            self._object_aliases = {}
            for oname in self.registered_objects:
                # TODO: think about other names of objects-as-attributes
                key = '_%s' % oname.replace('_', '__').replace('.', '_')
                self._object_aliases[key] = oname
        return self._object_aliases

    def __dir__(self):
        res = super(ClientSugar, self).__dir__()
        res += self.object_aliases.keys()
        res += self.plugins.registered_plugins
        return res

    def __getattr__(self, name):
        objname = self.object_aliases.get(name, None)
        if objname is not None:
            return self.get_obj(objname)

        if name in self.plugins:
            return self.plugins[name]

        raise AttributeError("'Client' object has no atribute %s" % name)

    def clean_caches(self):
        """ Clean client related caches
        """
        super(ClientSugar, self).clean_caches()
        self._object_aliases = None
