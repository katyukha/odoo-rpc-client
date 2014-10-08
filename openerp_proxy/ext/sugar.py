import numbers

from openerp_proxy.orm.record import ObjectRecords
from openerp_proxy.orm.record import RecordList
from openerp_proxy.core import ERP_Proxy
#from openerp_proxy.orm.record import get_record_list_class


class ObjectSugar(ObjectRecords):
    """ Provides aditional methods to work with data
    """

    def search_record(self, *args, **kwargs):
        kwargs['limit'] = 1
        return self.search_records(*args, **kwargs)[0]

    # Overriden to be able to read items using index operation
    def __getitem__(self, name):
        if isinstance(name, (numbers.Integral, list, tuple)):
            return self.read_records(name)
        raise KeyError("Bad key: %s! Only integer or list of intergers allowed" % name)

    def __call__(self, name, *args, **kwargs):
        """ Performs name_search by specified 'name'
        """
        res = self.name_search(name, *args, **kwargs)
        ids = [i[0] for i in res]
        if len(ids) == 1:
            return self[ids[0]]  # user previously defined __getitem__ functionality
        return RecordList(self, ids=ids)


class ERP_Proxy_Sugar(ERP_Proxy):

    def __init__(self, *args, **kwargs):
        super(ERP_Proxy_Sugar, self).__init__(*args, **kwargs)
        self._object_aliases = None

    @property
    def object_aliases(self):
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
