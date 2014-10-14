from openerp_proxy.orm.record import RecordList


class RecordListData(RecordList):
    """ Extend record list to add aditional method to work with lists of records
    """

    def as_table(self, fields=None):
        if fields is None:
            res = "     ID | Name\n"
            res += "\n".join(("%7s | %s" % (r.id, r._name) for r in self))
            return res
        raise NotImplementedError()



