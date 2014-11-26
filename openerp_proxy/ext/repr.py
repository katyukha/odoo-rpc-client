""" This module privides additional representation capabilities
of RecordList class, like representation as HTML table with
ability to highlight specific rows, which is usefule when
used inside IPython notebook

"""

from openerp_proxy.orm.record import RecordList
from openerp_proxy.orm.record import Record
from IPython.display import HTML


class HTMLTable(object):
    """ HTML Table representation object for RecordList

        :param recordlist: record list to create represetation for
        :type recordlist: RecordList instance
        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance)
        :type fields: list(string | callable)
        :param highlight_row: function to check if row to be highlighted
        :type highlight_row: callable(record) -> bool
    """
    def __init__(self, recordlist, fields, **kwargs):
        self._recordlist = recordlist
        self._fields = fields
        self._highlighters = {}
        if kwargs.get('highlight_row', False):
            self._highlighters['#ffff99'] = kwargs['highlight_row']
        self._highlighters.update(kwargs.get('highlighters', {}))

    def _get_field(self, record, field):
        """ Returns value for requested field.
            fields should be dotted path to value of record like::
                'product_id.categ_id.name'
            or function to get value from record like::
                lambda r: r.product_id.categ_id.name

            :param record: Record instance to get field from
            :type: Record instance
            :param field: path to field or function to get value from record
            :type: string|func(record)->value
            :return: requested value
        """

        if callable(field):
            return field(record)

        fields = field.split('.')
        r = record
        while fields:
            field = fields.pop(0)
            try:
                r = r[field]  # try to get normal field
            except KeyError:
                try:
                    r = r[int(field)]  # try to get by index (to allow to get value from *2m fields)
                except (KeyError, ValueError):
                    try:
                        r = getattr(r, field)  # try to get attribute
                        if callable(r):        # and if attribute is callable then call it
                            r = r()
                    except AttributeError:
                        raise
        return r

    def highlight_record(self, record):
        """ Checks all highlighters related to this representation object
            and return color of firest match highlighter
        """
        for color, highlighter in self._highlighters.items():
            if highlighter(record):
                return color
        return False

    def _repr_html_(self):
        """ HTML representation
        """
        table = "<table>%s</table>"
        trow = "<tr>%s</tr>"
        throw = '<tr style="background: %s">%s</tr>'
        tcaption = "<caption>%s</caption>" % self._recordlist
        theaders = "".join(("<th>%s</th>" % field for field in self._fields))
        data = ""
        data += tcaption
        data += trow % theaders
        for record in self._recordlist:
            tdata = "".join(("<td>%s</td>" % self._get_field(record, field) for field in self._fields))
            hcolor = self.highlight_record(record)
            if hcolor:
                data += throw % (hcolor, tdata)
            else:
                data += trow % tdata
        return table % data


class RecordListData(RecordList):
    """ Extend record list to add aditional methods related to RecordList representation
    """

    def as_table(self, fields=None):
        """ Table representation of record list

            At this moment hust (ID | Name) table
        """
        if fields is None:
            res = "     ID | Name\n"
            res += "\n".join(("%7s | %s" % (r.id, r._name) for r in self))
            return res
        raise NotImplementedError()

    def as_html_table(self, *fields, **kwargs):
        """ HTML Table representation object for RecordList

            :param fields: list of fields to display. each field should be string
                           with dot splitted names of related object, or callable
                           of one argument (record instance)
            :type fields: list(string | callable)
            :param highlight_row: function to check if row to be highlighted
                                  also *openerp_proxy.utils.r_eval* may be used
            :type highlight_row: callable(record) -> bool
        """
        return HTMLTable(self, fields, **kwargs)


class HTMLRecord(Record):
    """ Adds HTML representation of record
    """

    def as_html(self, fields=None):
        self.read(fields)
        table_tmpl = u"<table><caption>Record %s</caption><tr><th>Column</th><th>Value</th></tr>%s</table>"
        row_tmpl = u"<tr><th>%s</th><td>%s</td></tr>"

        body = ""
        for col_name, col_data in self._columns_info.iteritems():
            row = row_tmpl % (col_data.get('string', col_name), self[col_name])
            body += row
        return HTML(table_tmpl % (self._name, body))



