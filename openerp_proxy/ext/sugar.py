"""
Provides some syntax sugar to ease acces to objects, records, etc

"""

import numbers

from openerp_proxy.orm.record import ObjectRecords
from openerp_proxy.orm.record import RecordList
from openerp_proxy.core import ERP_Proxy
#from openerp_proxy.orm.record import get_record_list_class


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
                moves = obj[125,126,127]  # returns record list of three move records
                                        # for IDS 125, 126, 127

        2. name_search

           Calling object with record name as first argument will execute name
           search on passed name::

                so = so_obj('SO005')   # Returns sale order with name 'SO005'
                so2 = so_obj('5')      # If there are more than one records found by name
                                        # RecordList will be returned. In this case
                                        # this call may return list which will
                                        # contain for example sale orders with
                                        # names like 'SO005', 'SO015', etc.

        3. simple search.

           If pass domain as first argument when calling object, then *search_records*
           method will be called with all arguments forwarded::

               res = so_obj([('state','=','done')], limit=10)
               # res -> RecordList('sale.order', length=10)

           Also for simple searches without joins it is posible to pass just only keyword arguments
           which all will be converted to domain::

               res = so_obj(state='done')

            But note, that in last way, **all keyword arguments will be converted to domain,
            no one of them will be forwarded to search_records**, so it is not posible,
            for example, to limit results at this moment


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
        raise KeyError("Bad key: %s! Only integer or list of intergers allowed" % name)

    def __call__(self, *args, **kwargs):
        """ Performs name_search by specified 'name'

            (below under name 'name' i mean first of 'args')
            if name is list or tuple, then search_records will be called
            if name not passed or name is None, then kwargs will be used to build search domain
                and search_records will be called
            else name_search will run
        """
        args = list(args)
        name = args.pop(0) if args else None

        if name is None:
            domain = [(k, '=', v) for k, v in kwargs.iteritems()]
            return self.search_records(domain, *args)

        if isinstance(name, (list, tuple)):
            return self.search_records(name, *args, **kwargs)

        res = self.name_search(name, *args, **kwargs)
        ids = [i[0] for i in res]
        if len(ids) == 1:
            return self[ids[0]]  # user previously defined __getitem__ functionality
        return RecordList(self, ids=ids)


class ERP_Proxy_Sugar(ERP_Proxy):
    """ Provides some syntax sugar for ERP_Proxy class

        As one of it's features is ability to access objects as
        attributes via *object aliaces*. Each aliase is object name
        with underscores replaced by double underscores and dots replaced by
        single underscores and prefixed by underscore.

        For example::

            proxy._stock_move == proxy['stock.move'] == proxy.get_obj('stock.move')

    """

    def __init__(self, *args, **kwargs):
        super(ERP_Proxy_Sugar, self).__init__(*args, **kwargs)
        self._object_aliases = None

    @property
    def object_aliases(self):
        """ Property, that holds list of all object aliases for this ERP_Proxy instance
        """
        if self._object_aliases is None:
            self._object_aliases = {}
            for oname in self.registered_objects:
                # TODO: think about other names of aobjects-as-attributes
                key = '_%s' % oname.replace('_', '__').replace('.', '_')
                self._object_aliases[key] = oname
        return self._object_aliases

    def __dir__(self):
        res = dir(super(ERP_Proxy_Sugar, self))
        res += self.object_aliases.keys()
        return res

    def __getattr__(self, name):
        objname = self.object_aliases.get(name, None)
        if objname is None:
            raise AttributeError("'ERP_Proxy' object has no atribute %s" % name)
        return self.get_obj(objname)
