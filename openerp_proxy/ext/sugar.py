import numbers

from openerp_proxy.orm.record import ObjectRecords
from openerp_proxy.orm.record import RecordListBase
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

    def __call__(self, name):
        """ Performs name_search by specified 'name'
        """
        res = self.name_search(name)
        ids = [i[0] for i in res]
        if len(ids) == 1:
            return self[ids[0]]  # user previously defined __getitem__ functionality
        return RecordListBase(self, ids=ids)

