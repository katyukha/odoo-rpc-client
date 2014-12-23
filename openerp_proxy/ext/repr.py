""" This module privides additional representation capabilities
of RecordList class, like representation as HTML table with
ability to highlight specific rows, which is usefule when
used inside IPython notebook

"""

from openerp_proxy.orm.record import RecordList
from openerp_proxy.orm.record import Record
from IPython.display import HTML

from openerp_proxy.utils import ustr as _


class FieldNotFoundException(Exception):
    def __init__(self, obj, field, original_exc=None):
        self.field = field
        self.obj = obj
        self.orig_exc = original_exc

    def __unicode__(self):
        return u"Field %s not found in obj %s" % (_(self.field), _(self.obj))


class HField(object):
    """ Describes how to get a field.
        Primaraly used in html representation logic.

        :param field: path to field or function to get value from record
                      if path is string, then it should be dot separated list of
                      fields/subfields to get value from. for example
                      ``sale_line_id.order_id.name`` or ``picking_id.move_lines.0.location_id``
        :type field: string|func(record)->value
        :param string name: name of field. (optional)
                            if specified, then this value will be used in column header of table.
        :param bool silent: If set to True, then not exceptions will be raised and *default* value
                            will be returned. (default=False)
        :param default: default value to be returned if field not found. default=None
    """

    def __init__(self, field, name=None, silent=False, default=None):
        self._field = field
        self._name = name
        self._silent = silent
        self._default = default

    @classmethod
    def _get_field(cls, obj, name):
        """ Try to get field named *name* from object *obj*
        """
        try:
            res = obj[name]
        except:
            try:
                res = obj[int(name)]
            except:
                try:
                    res = getattr(obj, name)
                except:
                    raise FieldNotFoundException(obj, name)
        return res

    def get_field(self, record):
        """ Returns requested value from specified record (object)

            :param record: Record instance to get field from (also should work on any other object)
            :type record: Record instance
            :return: requested value
        """

        if callable(self._field):
            return self._field(record)

        fields = self._field.split('.')
        r = record
        while fields:
            field = fields.pop(0)
            try:
                r = self._get_field(r, field)
                if callable(r):        # and if attribute is callable then call it
                    r = r()
            except FieldNotFoundException:
                if not self._silent:   # reraise exception if not silent
                    raise
                else:                  # or return default value
                    r = self._default
                    break
        return r

    def __call__(self, record):
        """ Get value from specified record
        """
        return self.get_field(record)

    def __unicode__(self):
        return _(self._name) if self._name is not None else _(self._field)


class HTMLTable(object):
    """ HTML Table representation object for RecordList

        :param recordlist: record list to create represetation for
        :type recordlist: RecordList instance
        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance) or *HField* instance or
                       tuple(field_path|callable, field_name)
        :type fields: list(string | callable | HField instance | tuple(field, name))
        :param dict highlighters: dictionary in format:
                                      {color: callable(record)->bool}
                                  where *color* any color suitable for HTML and
                                  callable is function of *Record instance)* which decides,
                                  if record should be colored by this color
        :param highlight_row: function to check if row to be highlighteda (deprecated)
                              (old_style)
        :type highlight_row: callable(record) -> bool
    """
    def __init__(self, recordlist, fields, **kwargs):
        self._recordlist = recordlist
        self._fields = []
        for field in fields:
            if isinstance(field, HField):
                self._fields.append(field)
            elif isinstance(field, basestring):
                self._fields.append(HField(field))
            elif callable(field):
                self._fields.append(HField(field))
            elif isinstance(field, (tuple, list)) and len(field) == 2:
                self._fields.append(HField(field[0], name=field[1]))
            else:
                raise ValueError('Unsupported field type: %s' % repr(field))
        self._highlighters = {}
        if kwargs.get('highlight_row', False):
            self._highlighters['#ffff99'] = kwargs['highlight_row']
        self._highlighters.update(kwargs.get('highlighters', {}))

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
        table = u"<table>%s</table>"
        trow = u"<tr>%s</tr>"
        throw = u'<tr style="background: %s">%s</tr>'
        tcaption = u"<caption>%s</caption>" % _(self._recordlist)
        theaders = u"".join((u"<th>%s</th>" % _(field) for field in self._fields))
        data = u""
        data += tcaption
        data += trow % theaders
        for record in self._recordlist:
            tdata = u"".join((u"<td>%s</td>" % _(field(record)) for field in self._fields))
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
        """ Returns HTML representation of this Record

           :param list fields: list of field names to display in HTML representation
           :return: ipython's HTML object representing this record
        """
        self.read(fields)
        table_tmpl = u"<table><caption>Record %s</caption><tr><th>Column</th><th>Value</th></tr>%s</table>"
        row_tmpl = u"<tr><th>%s</th><td>%s</td></tr>"

        body = ""
        for col_name, col_data in self._columns_info.iteritems():
            row = row_tmpl % (col_data.get('string', col_name), self[col_name])
            body += row
        return HTML(table_tmpl % (self._name, body))
