""" This module provides additional representation capabilities
of RecordList class, like representation as HTML table with
ability to highlight specific rows, which is useful when
used inside IPython notebook

"""

# TODO: rename to IPython or something like that
import os
import six
import csv
import os.path
import tempfile
from IPython.display import HTML, FileLink

from .. import (Client,
                Session)
from ..orm import (RecordList,
                   Record,
                   Object)
from ..service.report import (Report,
                              ReportResult,
                              ReportService)


from ..utils import ustr as _
from ..utils import (AttrDict,
                     makedirs)


# TODO: use enviroment var or some sort of config
# Here we use paths based on current directory, because default IPython
# notebook configuration does not allow to access files located somewere else
GEN_FILE_PATH = os.path.normpath(os.path.join('.', 'tmp'))
CSV_PATH = os.path.join(GEN_FILE_PATH, 'csv')
REPORTS_PATH = os.path.join(GEN_FILE_PATH, 'reports')

# Create required paths
makedirs(CSV_PATH)
makedirs(REPORTS_PATH)

# HTML Templates
TMPL_INFO_WITH_HELP = u"""
<div class="container-fluid">
    <div class="row">
        <div class="col-md-7 col-lg-7">%(info)s</div>
        <div style="display:inline-block" class="panel panel-default col-md-5 col-lg-5">
            <div class="panel-heading">Info</div>
            <div class="panel-body">%(help)s</div>
        </div>
    </div>
</div>
"""

TMPL_TABLE = u"""
<table class="table table-bordered table-condensed %(extra_classes)s" style="margin-left:0;%(styles)s">
<caption>%(caption)s</caption>
%(rows)s
</table>
"""

TMPL_TABLE_ROW = u"<tr>%s</tr>"
TMPL_TABLE_DATA = u"<td>%s</td>"
TMPL_TABLE_HEADER = u"<th>%s</th>"


def th(val):
    return TMPL_TABLE_HEADER % _(val)


def td(val):
    return TMPL_TABLE_DATA % _(val)


def tr(*args):
    return TMPL_TABLE_ROW % u"".join(args)


def describe_object_html(data, caption='', help='', table_styles=''):
    """ Converts dictionary data to html table string

        :param dict data: dictionary like object. must contain .items() method
                          represents object info to be displayed in table
        :param str caption: table's caption
        :param str help: help message to be displayed near table
        :param str table_styles: string with styles for table
    """
    html_data = u"".join((tr(th(k), td(v)) for k, v in data.items()))

    table = TMPL_TABLE % {'styles': table_styles,
                          'caption': caption,
                          'rows': html_data,
                          'extra_classes': ''}
    return TMPL_INFO_WITH_HELP % {'info': table, 'help': help}


class FieldNotFoundException(Exception):
    """ Exception raised when HField cannot find field in object been processed
    """
    def __init__(self, obj, name, hfield, original_exc=None):
        self.hfield = hfield
        self.name = name
        self.obj = obj
        self.orig_exc = original_exc

    @property
    def message(self):
        return u"Field %s not found in obj %s while calculation hfield %s" % (_(self.field), _(self.obj), self.hfield)

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


@six.python_2_unicode_compatible
class HField(object):
    """ Describes how to get a field.
        Primaraly used in html representation logic.

        :param field: path to field or function to get value from record
                      if path is string, then it should be dot separated list of
                      fields/subfields to get value from. for example
                      ``sale_line_id.order_id.name`` or ``picking_id.move_lines.0.location_id``
        :type field: str | func(record)->value
        :param str name: name of field. (optional)
                            if specified, then this value will be used in column header of table.
        :param bool silent: If set to True, then not exceptions will be raised and *default* value
                            will be returned. (default=False)
        :param default: default value to be returned if field not found. default=None
        :param HField parent: (for internal usage) parent field. First get value of parent field
                              for record, and then get value of current field based on value
                              of parent field: ( self.get_field(self._parent.get_field(record)) )
        :param args: if specified, then it means that field is callable, and *args* should be passed
                     to it as positional arguments. This may be useful to call *as_html_table* method
                     of internal field. for example::

                         HField('picking_id.move_lines.as_html_table',
                                args=('id', '_name', HField('location_id._name', 'Location')))

                     or better way::

                         HField('picking_id.move_lines.as_html_table').with_args(
                             'id',
                             '_name',
                             HField('location_id._name', 'Location')
                         )

        :type args: list | tuple
        :param dict kwargs: same as *args* but for keyword arguments
    """

    def __init__(self, field, name=None, silent=False, default=None, parent=None, args=None, kwargs=None):
        self._field = field
        self._name = name
        self._silent = silent
        self._default = default
        self._parent = parent
        self._args = tuple() if args is None else args
        self._kwargs = dict() if kwargs is None else kwargs

    def F(self, field, **kwargs):
        """ Create chained field
            Could be used for complicated field.
            for example::

                HField('myfield.myvalue', default={'a': 5}).F('a')
        """
        return HField(
            field,
            parent=self,
            name=kwargs.get('name', self._name),
            silent=kwargs.get('silent', self._silent),
            default=kwargs.get('default', self._default),
            args=kwargs.get('args', self._args),
            kwargs=kwargs.get('kwargs', self._kwargs),
        )

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
            :type record: Record
            :return: requested value
        """
        # process parent field
        if self._parent is not None:
            record = self._parent.get_field(record)

        # check if field is callable
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
            :type record: Record
            :return: value of self-field of record
        """
        return self.get_field(record)

    def __str__(self):
        return _(self._name) if self._name is not None else _(self._field)


# TODO: also implement vertical table orientation, which could be usefult for
# comparing few records or reuse same code for displaying single record.
class HTMLTable(HTML):
    """ HTML Table representation object for RecordList

        :param recordlist: record list to create represetation for
        :type recordlist: RecordList
        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance) or *HField* instance or
                       tuple(field_path|callable, field_name)
        :type fields: list(str | callable | HField instance | tuple(field, name))
        :param str caption: String to be used as table caption
        :param dict highlighters: dictionary in format::

                                      {color: callable(record)->bool}

                                  where *color* any color suitable for HTML and
                                  callable is function of *Record instance* which decides,
                                  if record should be colored by this color
    """
    def __init__(self, recordlist, fields, caption=None, highlighters=None, **kwargs):
        self._recordlist = recordlist
        self._caption = u"HTMLTable"
        self._fields = []
        self._highlighters = {}

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
        theaders = u"".join((th(header) for header in self.iheaders))
        help = u"Note, that You may use <i>.to_csv()</i> method of this table to export it to CSV format"
        table = (u"<div><div>{help}</div>"
                 u"<table class='table table-bordered table-condensed table-striped'>"
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
            tdata = u"".join((td(fval) for fval in record['row']))
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
        # Python 2/3 compatability
        if six.PY3:
            adapt = lambda s: s
            fmode = 'wt'
        else:
            fmode = 'wb'
            adapt = lambda s: s.encode('utf-8')

        tmp_file = tempfile.NamedTemporaryFile(mode=fmode, dir=CSV_PATH, suffix='.csv', delete=False)
        with tmp_file as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(tuple((adapt(h) for h in self.iheaders)))
            for record in self.irecords:
                csv_writer.writerow(tuple((adapt(r) for r in record['row'])))
        return FileLink(os.path.join(CSV_PATH, os.path.split(tmp_file.name)[-1]))


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
            :return: HTMLTable
        """
        if not fields:
            fields = ('id', '_name')
        return HTMLTable(self, fields, **kwargs)

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (u"To get table representation of data call method<br/>"
                     u"&nbsp;<i>.as_html_table</i><br/>"
                     u"passing as arguments fields You want to see in resulting table<br/>"
                     u"for better information get doc on as_html_table method:<br/>"
                     u"&nbsp;<i>.as_html_table?</i><br/>"
                     u"example of using this mehtod:<br/>"
                     u"&nbsp;<i>.as_html_table('id','name','_name')</i><br/>"
                     u"Here <i>_name</i> field is aliase for result of <i>name_get</i> method"
                     u"called on record")

        return describe_object_html({
            "Object": self.object,
            "Client": self.object.proxy.get_url(),
            "Record count": self.length,
        }, caption=_(self), help=help_text)


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
           :rtype: HTML
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
        help_text = (u"To get HTML Table representation of this record call method:<br/>"
                     u"&nbsp;<i>.as_html()</i><br/>"
                     u"Optionaly You can pass list of fields You want to see:<br/>"
                     u"&nbsp;<i>.as_html('name', 'origin')</i><br/>"
                     u"for better information get doc on <i>as_html</i> method:<br/>"
                     u"&nbsp;<i>.as_html?</i><br/>")

        return describe_object_html({
            "Object": self._object,
            "Client": self._object.proxy.get_url(),
            "ID": self.id,
            "Name": self._name,
        }, caption=_(self), help=help_text)


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
        help_text = (u"To get information about columns access property<br/>"
                     u"&nbsp;<i>.columns_info</i><br/>"
                     u"Also there are available standard server-side methods:<br/>"
                     u"&nbsp;<i>search</i>, <i>read</i>, <i>write</i>, <i>unlink</i></br>"
                     u"And special methods provided <i>openerp_proxy's orm</i>:"
                     u"<ul style='margin-top:1px'>"
                     u"<li><i>search_records</i> - same as <i>search</i> but returns <i>RecordList</i> instance</li>"
                     u"<li><i>read_records</i> - same as <i>read</i> but returns <i>Record</i> or <i>RecordList</i> instance</li>"
                     u"<ul><br/>")

        return describe_object_html({
            "Name": self.model.name,
            "Client": self.proxy.get_url(),
            "Model": self.model.model,
            "Record count": self.search([], count=True),
        }, caption=_(self.model.name), help=help_text)


class ClientHTML(Client):
    """ HTML modifications for Client class
    """

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (u"To get list of registered objects for thist database<br/>"
                     u"access <i>registered_objects</i> property:<br/>"
                     u"&nbsp;<i>.registered_objects</i>"
                     u"To get Object instance just call <i>get_obj</i> method<br/>"
                     u"&nbsp;<i>.get_obj(name)</i><br/>"
                     u"where <i>name</i> is name of Object You want to get"
                     u"<br/>or use get item syntax instead:</br>"
                     u"&nbsp;<i>[name]</i>")

        return describe_object_html({
            "Host": self.host,
            "Port": self.port,
            "Protocol": self.protocol,
            "Database": self.dbname,
            "login": self.username,
        }, caption=u"RPC Client", help=help_text)


class AvailableReportsInfo(AttrDict):
    """ Simple class to get HTML representation of available reports
    """
    def __init__(self, *args, **kwargs):
        super(AvailableReportsInfo, self).__init__(*args, **kwargs)

        self._fields = None
        self._html_table = None

    @property
    def default_fields(self):
        """ Default fields displayed in resulting HTML table
        """
        if self._fields is None:
            self._fields = [
                HField('report_action.report_name',
                       'report service name',
                       silent=True),
                HField('report_action.name',
                       'report name',
                       silent=True),
                HField('report_action.model',
                       'report model',
                       silent=True),
                HField('report_action.help',
                       'report help info',
                       silent=True),
            ]
        return self._fields

    def as_html_table(self, fields=None):
        """ Generates HTMLTable representation for this reports info

            :param fields: list of fields to display instead of defaults
            :return: generated HTMLTable instanse
            :rtype: HTMLTable
        """
        fields = self.default_fields if fields is None else fields
        return HTMLTable(sorted(self.values(), key=lambda x: x.name),
                         fields,
                         caption=u'Available reports')

    def _repr_html_(self):
        """ HTML representation for reports info
        """
        if self._html_table is None:
            self._html_table = self.as_html_table()
        return self._html_table._repr_html_()


class ReportServiceExt(ReportService):
    """ Adds html representation for report service
    """

    def _get_available_reports(self):
        """ Returns list of reports registered in system
        """
        return AvailableReportsInfo(
            super(ReportServiceExt, self)._get_available_reports())

    def _repr_html_(self):
        return ("<div>This is report service. <br/>"
                "To get list of available reports<br/>"
                "You can access <i>available_reports</i><br/>"
                "property of this service: "
                "<pre>.available_reports</pre>"
                "</div>")


class ReportExt(Report):
    def _repr_html_(self):
        help_text = (u"This is report representation.<br/>"
                     u"call <i>generate<i> method to generate new report<br/>"
                     u"&nbsp;<i>.generate([1, 2, 3])</i><br/>"
                     u"Also <i>generate</i> method can receive <br/>"
                     u"RecordList or Record instance as first argument.<br/>"
                     u"For more information look in "
                     u"<a href='http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.service.html#module-openerp_proxy.service.report'>documentation</a>")

        return describe_object_html({
            "Name": self.report_action.name,
            "Service name": self.name,
            "Model": self.report_action.model,
        }, caption=u'Report %s' % _(self.report_action.name), help=help_text)


class ReportResultExt(ReportResult):
    """ Adds HTML representation of Report Result
    """

    def _repr_html_(self):
        # TODO: refactor this
        path = os.path.join(REPORTS_PATH, self.path)
        return FileLink(self.save(path).path)._repr_html_()


class IPYSession(Session):
    def _repr_html_(self):
        """ Provides HTML representation of session (Used for IPython)
        """
        def _get_data():
            for url in self._databases.keys():
                index = self._index_url(url)
                aliases = (_(al) for al, aurl in self.aliases.items() if aurl == url)
                yield (url, index, u", ".join(aliases))
        hrow = u"<tr><th>DB URL</th><th>DB Index</th><th>DB Aliases</th></tr>"
        help_text = (u"To get connection just call<br/> <ul>"
                     u"<li>session.<b>aliase</b></li>"
                     u"<li>session[<b>index</b>]</li>"
                     u"<li>session[<b>aliase</b>]</li> "
                     u"<li>session[<b>url</b>]</li>"
                     u"<li>session.get_db(<b>url</b>|<b>index</b>|<b>aliase</b>)</li></ul>")

        data = u""
        for row in _get_data():
            data += tr(*[td(i) for i in row])

        table = TMPL_TABLE % {'styles': '',
                              'extra_classes': 'table-striped',
                              'caption': u"Previous connections",
                              'rows': hrow + data}

        return TMPL_INFO_WITH_HELP % {'info': table, 'help': help_text}
