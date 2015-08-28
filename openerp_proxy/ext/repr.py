""" This module provides additional representation capabilities
of RecordList class, like representation as HTML table with
ability to highlight specific rows, which is useful when
used inside IPython notebook

"""

# TODO: rename to IPython or something like that

import six
import csv
import tempfile

from openerp_proxy.orm.record import RecordList
from openerp_proxy.orm.record import Record
from openerp_proxy.orm.object import Object
from openerp_proxy.core import Client
from openerp_proxy.utils import AttrDict

from IPython.display import HTML, FileLink

from openerp_proxy.utils import ustr as _


class FieldNotFoundException(Exception):
    def __init__(self, obj, field, original_exc=None):
        self.field = field
        self.obj = obj
        self.orig_exc = original_exc

    @property
    def message(self):
        return u"Field %s not found in obj %s" % (_(self.field), _(self.obj))

    # TODO: implement correct behavior. It fails in IPython notebook with
    # UnicodeEncodeError because of python's standard warnings module
    #def __unicode__(self):
        #return message

    def __str__(self):
        # converting to ascii because of python's warnings module fails in
        # UnicodeEncodeError when no-ascii symbols present in str(exception)
        return self.message.encode('ascii', 'backslashreplace')

    def __repr__(self):
        return str(self)


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
        :param args: if specified, then it means that field is callable, and *args* should be passed
                     to it as positional arguments. This may be useful to call *as_html_table* method
                     of internal field. for example::

                         HField('picking_id.move_lines.as_html_table',
                                args=('id', '_name', HField('location_id._name', 'Location')))

                    or better way::

                         HField('picking_id.move_lines.as_html_table').\
                             with_args('id', '_name', HField('location_id._name', 'Location'))

        :type args: list|tuple
        :param dict kwargs: same as *args* but for keyword arguments
    """

    def __init__(self, field, name=None, silent=False, default=None, args=None, kwargs=None):
        self._field = field
        self._name = name
        self._silent = silent
        self._default = default
        self._args = tuple() if args is None else args
        self._kwargs = dict() if kwargs is None else kwargs

    def with_args(self, *args, **kwargs):
        """ If field is string pointing to function (or method),
            all arguments and keyword arguments passed to this method,
            will be passed to field (function).

            For example::

                HField('picking_id.move_lines.as_html_table').with_args(
                    'id', '_name', HField('location_id._name', 'Location'))

            This arguments ('id', '_name', HField('location_id._name', 'Location'))
            will be passed to ``picking_id.move_lines.as_html_table`` method

            :return: self
        """
        self._args = args
        self._kwargs = kwargs
        return self

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
            return self._field(record, *self._args, **self._kwargs)

        fields = self._field.split('.')
        r = record
        while fields:
            field = fields.pop(0)
            try:
                r = self._get_field(r, field)
                if callable(r) and fields:  # and if attribute is callable and
                                            # it is not last field then call
                                            # it without arguments
                    r = r()
                elif callable(r) and not fields:  # last field and if is callable
                    r = r(*self._args, **self._kwargs)
            except:  # FieldNotFoundException:
                if not self._silent:   # reraise exception if not silent
                    raise
                else:                  # or return default value
                    r = self._default
                    break
        return r

    def __call__(self, record):
        """ Get value from specified record

            :param record: object to get field from
            :type record: usualy Record instance
            :return: value of self-field of record
        """
        return self.get_field(record)

    def __unicode__(self):
        return _(self._name) if self._name is not None else _(self._field)


# TODO: also implement vertical table orientation, which could be usefult for
# comparing few records or reuse same code for displaying single record.
class HTMLTable(HTML):
    """ HTML Table representation object for RecordList

        :param recordlist: record list to create represetation for
        :type recordlist: RecordList instance
        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance) or *HField* instance or
                       tuple(field_path|callable, field_name)
        :type fields: list(string | callable | HField instance | tuple(field, name))
        :param dict highlighters: dictionary in format::

                                      {color: callable(record)->bool}

                                  where *color* any color suitable for HTML and
                                  callable is function of *Record instance* which decides,
                                  if record should be colored by this color
        :param highlight_row: function to check if row to be highlighteda (**deprecated**)
                              (old_style)
        :type highlight_row: callable(record) -> bool
        :param str caption: String to be used as table caption
    """
    def __init__(self, recordlist, fields, caption=None, highlighters=None, **kwargs):
        self._recordlist = recordlist
        self._caption = u"HTMLTable"

        self._fields = []
        self._highlighters = {}
        if kwargs.get('highlight_row', False):
            self._highlighters['#ffff99'] = kwargs['highlight_row']

        self.update(fields=fields, caption=caption, highlighters=highlighters, **kwargs)

    def update(self, fields=None, caption=None, highlighters=None, **kwargs):
        """ This method is used to change HTMLTable initial data, thus, changing representation
            Can be used for example, when some function returns partly configured HTMLTable instance,
            but user want's to display more fields for example, or add some custom highlighters

            arguments same as for constructor, except 'recordlist' arg, which is absent in this method

            :return: self
        """
        self._caption = _(self._recordlist) if caption is None else _(caption)
        fields = [] if fields is None else fields
        for field in fields:
            if isinstance(field, HField):
                self._fields.append(field)
            elif isinstance(field, six.string_types):
                self._fields.append(HField(field))
            elif callable(field):
                self._fields.append(HField(field))
            elif isinstance(field, (tuple, list)) and len(field) == 2:
                self._fields.append(HField(field[0], name=field[1]))
            else:
                raise ValueError('Unsupported field type: %s' % repr(field))

        if highlighters is not None:
            self._highlighters.update(highlighters)

        return self

    @property
    def caption(self):
        """ Table caption
        """
        return self._caption

    @property
    def fields(self):
        """ List of fields of table.
            :type: list of HField instances
        """
        return self._fields

    @property
    def iheaders(self):
        """ Iterator in headers
            :type: list of unicode strings
        """
        return (_(field) for field in self.fields)

    @property
    def irecords(self):
        """ Returns iterator on records, where each record
            is dictionary of two fields: 'row', 'color'.

            'row' dictionary field is iterator in fields of this record

            so result of this property colud be used to build representation
        """
        def preprocess_field(field):
            """ Process some special cases of field to be correctly displayed
            """
            if isinstance(field, HTML):
                return field._repr_html_()
            return _(field)

        for record in self._recordlist:
            yield {
                'color': self.highlight_record(record),
                'row': (preprocess_field(field(record)) for field in self.fields),
            }

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
        theaders = u"".join((u"<th>%s</th>" % header for header in self.iheaders))
        help = u"Note, that You may use <i>.to_csv()</i> method of this table to export it to CSV format"
        table = (u"<div><div>{help}</div><table>"
                 u"<caption>{self.caption}</caption>"
                 u"<tr>{headers}</tr>"
                 u"%s</table>"
                 u"<div>").format(self=self,
                                  headers=theaders,
                                  help=help)
        trow = u"<tr>%s</tr>"
        throw = u'<tr style="background: %s">%s</tr>'
        data = u""
        for record in self.irecords:
            hcolor = record['color']
            tdata = u"".join((u"<td>%s</td>" % fval for fval in record['row']))
            if hcolor:
                data += throw % (hcolor, tdata)
            else:
                data += trow % tdata
        return table % data

    def to_csv(self):
        """ Write table to CSV file and return FileLink object for it

            :return: instance of FileLink
            :rtype: FileLink
        """
        CSV_PATH = './tmp/csv/' # TODO: use enviroment var or some sort of config
        import os.path
        import os

        try:
            os.makedirs(CSV_PATH)
        except os.error:
            pass

        tmp_file = tempfile.NamedTemporaryFile(dir=CSV_PATH, suffix='.csv', delete=False)
        with tmp_file as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(tuple((h.encode('utf-8') for h in self.iheaders)))
            for record in self.irecords:
                csv_writer.writerow(tuple((r.encode('utf-8') for r in record['row'])))
        return FileLink(CSV_PATH + os.path.split(tmp_file.name)[-1])


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

    def as_html_list(self):
        """ HTML List representation of RecordList
        """
        html = u"<div>%s</div>"
        tlist = u"<ul>%s</ul>"
        tli = u"<li><i>%d</i>: %s</li>"

        data = ""
        for rec in self:
            data += tli % (rec.id, rec._name)
        return HTML(html % (tlist % data))

    def as_html_table(self, *fields, **kwargs):
        """ HTML Table representation object for RecordList

            :param fields: list of fields to display. each field should be string
                        with dot splitted names of related object, or callable
                        of one argument (record instance) or *HField* instance or
                        tuple(field_path|callable, field_name)
            :type fields: list(string | callable | HField instance | tuple(field, name))
            :param dict highlighters: dictionary in format::

                                        {color: callable(record)->bool}

                                    where *color* any color suitable for HTML and
                                    callable is function of *Record instance* which decides,
                                    if record should be colored by this color
            :param highlight_row: function to check if row to be highlighteda (**deprecated**)
                                (old_style)
            :type highlight_row: callable(record) -> bool
            :param str caption: String to be used as table caption
            :return: HTMLTable instance
        """
        if not fields:
            fields = ('id', '_name')
        return HTMLTable(self, fields, **kwargs)

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        html = u"<div>%s</div>"
        ttable = u"<table style='display:inline-block'>%s</table>"
        trow = u"<tr>%s</tr>"
        tdata = u"<td>%s</td>"
        thead = u"<th>%s</th>"
        caption = u"<caption>%s</caption>" % _(self)
        help_text = (u"<div style='display:inline-block;vertical-align:top;margin-left:10px;'>"
                     u"To get table representation of data call method<br/>"
                     u"&nbsp;<i>.as_html_table</i><br/>"
                     u"passing as arguments fields You want to see in resulting table<br/>"
                     u"for better information get doc on as_html_table method:<br/>"
                     u"&nbsp;<i>.as_html_table?</i><br/>"
                     u"example of using this mehtod:<br/>"
                     u"&nbsp;<i>.as_html_table('id','name','_name')</i><br/>"
                     u"Here <i>_name</i> field is aliase for result of <i>name_get</i> method"
                     u"called on record"
                     u"</div>")

        def to_row(header, val):
            return trow % ((thead % _(header)) + (tdata % _(val)))

        data = u""
        data += to_row("Object", self.object)
        data += to_row("Proxy", self.object.proxy.get_url())
        data += to_row("Record count", len(self))

        table = ttable % (caption + data)

        return html % (table + help_text)


class HTMLRecord(Record):
    """ Adds HTML representation of record
    """

    def as_html(self, *fields):
        """ Returns HTML representation of this Record.
            By default show all record fields.
            all passed positional arguments are treated as field names to be displayed.
            Also posible to pass dotted related fields like ('move_dest_id.location_dest_id')
            Type of all positional arguments should be string or HField instances

           :param list fields: list of field names to display in HTML representation
           :return: ipython's HTML object representing this record
        """
        table_tmpl = u"<table><caption>Record %s</caption><tr><th>Column</th><th>Value</th></tr>%s</table>"
        row_tmpl = u"<tr><th>%s</th><td>%s</td></tr>"

        if not fields:
            fields = sorted((HField(col_name, name=col_data['string'])
                             for col_name, col_data in self._columns_info.items()
                             if col_name in self._object.simple_fields),
                            key=lambda x: _(x))
            self.read()
        else:
            # TODO: implement in better way this prefetching
            read_fields = (f.split('.')[0] for f in fields if isinstance(f, six.string_types) and f.split('.')[0] in self._columns_info)
            prefetch_fields = [f for f in read_fields if f not in self._data]
            self.read(prefetch_fields)

        parsed_fields = []
        for field in fields:
            if isinstance(field, HField):
                parsed_fields.append(field)
            elif isinstance(field, six.string_types):
                parsed_fields.append(HField(field))
            else:
                raise TypeError("Bad type of field %s" % repr(field))

        body = ""
        for field in parsed_fields:
            row = row_tmpl % (_(field), field(self))
            body += row

        return HTML(table_tmpl % (self._name, body))

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        html = u"<div>%s</div>"
        ttable = u"<table style='display:inline-block'>%s</table>"
        trow = u"<tr>%s</tr>"
        tdata = u"<td>%s</td>"
        thead = u"<th>%s</th>"
        caption = u"<caption>%s</caption>" % _(self)
        help_text = (u"<div style='display:inline-block;vertical-align:top;margin-left:10px;'>"
                     u"To get HTML Table representation of this record call method:<br/>"
                     u"&nbsp;<i>.as_html()</i><br/>"
                     u"Optionaly You can pass list of fields You want to see:<br/>"
                     u"&nbsp;<i>.as_html('name', 'origin')</i><br/>"
                     u"for better information get doc on <i>as_html</i> method:<br/>"
                     u"&nbsp;<i>.as_html?</i><br/>"
                     u"</div>")

        def to_row(header, val):
            return trow % ((thead % _(header)) + (tdata % _(val)))

        data = u""
        data += to_row("Object", self._object)
        data += to_row("Proxy", self._proxy.get_url())
        data += to_row("Name", self._name)

        table = ttable % (caption + data)

        return html % (table + help_text)


class ColInfo(AttrDict):
    """ Columns info capable for IPython's HTML representation
    """

    def __init__(self, obj, *args, **kwargs):
        self._html_table = None
        self._object = obj
        self._fields = None
        super(ColInfo, self).__init__(*args, **kwargs)

    @property
    def default_fields(self):
        """ Default fields displayed in resulting HTML table
        """
        if self._fields is None:
            def _get_selection(x):
                return u'<br/>\n'.join((u"%s - %s" % (_(repr(i[0])), _(i[1]))
                                        for i in x['info'].get('selection', []) or []))

            self._fields = [
                HField('name', silent=True),
                HField('info.string', silent=True),
                HField('info.type', silent=True),
                HField(_get_selection, silent=True, name='info.selection'),
                HField('info.help', silent=True),
                HField('info.readonly', silent=True),
                HField('info.required', silent=True),
                HField('info.relation_field', silent=True),
                HField('info.select', silent=True),
            ]
        return self._fields

    def as_html_table(self, fields=None):
        """ Generates HTMLTable representation for this columns info

            :param fields: list of fields to display instead of defaults
            :type fields: list
            :return: generated HTMLTable instanse
            :rtype: HTMLTable
        """
        fields = self.default_fields if fields is None else fields
        info_struct = [{'name': key,
                        'info': val} for key, val in self.items()]
        info_struct.sort(key=lambda x: x['name'])
        return HTMLTable(info_struct, fields, caption=u'Fields for %s' % _(self._object.name))

    def _repr_html_(self):
        """ HTML representation for columns info
        """
        if self._html_table is None:
            self._html_table = self.as_html_table()
        return self._html_table._repr_html_()


class ObjectHTML(Object):
    """ Modifies object's columns_info to return HTML capable representation of Fields
    """

    def _get_columns_info(self):
        res = super(ObjectHTML, self)._get_columns_info()
        return ColInfo(self, res)

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        model = self.model
        html = u"<div>%s</div>"
        ttable = u"<table style='display:inline-block'>%s</table>"
        trow = u"<tr>%s</tr>"
        tdata = u"<td>%s</td>"
        thead = u"<th>%s</th>"
        caption = u"<caption>Object '%s'</caption>" % _(model.name)
        help_text = (u"<div style='display:inline-block;vertical-align:top;margin-left:10px;'>"
                     u"To get information about columns access property<br/>"
                     u"&nbsp;<i>.columns_info</i><br/>"
                     u"Also there are available standard server-side methods:<br/>"
                     u"&nbsp;<i>search</i>, <i>read</i>, <i>write</i>, <i>unlink</i></br>"
                     u"And special methods provided <i>openerp_proxy's orm</i>:"
                     u"<ul style='margin-top:1px'>"
                     u"<li><i>search_records</i> - same as <i>search</i> but returns <i>RecordList</i> instance</li>"
                     u"<li><i>read_records</i> - same as <i>read</i> but returns <i>Record</i> or <i>RecordList</i> instance</li>"
                     u"<ul><br/>"
                     u"</div>")

        def to_row(header, val):
            return trow % ((thead % _(header)) + (tdata % _(val)))

        data = u""
        data += to_row("Name", model.name)
        data += to_row("Proxy", self.proxy.get_url())
        data += to_row("Model", model.model)
        data += to_row("Record count", self.search([], count=True))

        table = ttable % (caption + data)

        return html % (table + help_text)


class ClientHTML(Client):
    """ HTML modifications for Client class
    """

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        html = u"<div>%s</div>"
        ttable = u"<table style='display:inline-block'>%s</table>"
        trow = u"<tr>%s</tr>"
        tdata = u"<td>%s</td>"
        thead = u"<th>%s</th>"
        caption = u"<caption style='white-space:nowrap;font-weight: bold;'>%s</caption>" % self.get_url()
        help_text = (u"<div style='display:inline-block;vertical-align:top;margin-left:10px;'>"
                     u"To get list of registered objects for thist database<br/>"
                     u"access <i>registered_objects</i> property:<br/>"
                     u"&nbsp;<i>.registered_objects</i>"
                     u"To get Object instance just call <i>get_obj</i> method<br/>"
                     u"&nbsp;<i>.get_obj(name)</i><br/>"
                     u"where <i>name</i> is name of Object You want to get"
                     u"<br/>or use get item syntax instead:</br>"
                     u"&nbsp;<i>[name]</i>"
                     u"</div>")

        def to_row(header, val):
            return trow % ((thead % _(header)) + (tdata % _(val)))

        data = u""
        data += to_row("Host", self.host)
        data += to_row("Port", self.port)
        data += to_row("Protocol", self.protocol)
        data += to_row("Database", self.dbname)
        data += to_row("login", self.username)

        table = ttable % (caption + data)
        return html % (table + help_text)
