from openerp_proxy.orm.record import ObjectRecords
#from openerp_proxy.orm.record import RecordListBase
#from openerp_proxy.orm.record import get_record_list_class


class ObjectSugar(ObjectRecords):
    """ Provides aditional methods to work with data
    """

    def search_record(self, *args, **kwargs):
        kwargs['limit'] = 1
        return self.search_records(*args, **kwargs)[0]

    def read_record(self, *args, **kwargs):
        return self.read_records(*args, **kwargs)

