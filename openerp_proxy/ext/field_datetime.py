from ..orm.record import Record

import datetime


class RecordDateTime(Record):
    """ Provides auto conversion of datetime fields from
        string got from server to comparable datetime objects
    """

    def _get_field(self, ftype, name):
        res = super(RecordDateTime, self)._get_field(ftype, name)
        if res and ftype == 'date':
            return datetime.datetime.strptime(res, '%Y-%m-%d').date()
        elif res and ftype == 'datetime':
            return datetime.datetime.strptime(res, '%Y-%m-%d %H:%M:%S')
        return res
