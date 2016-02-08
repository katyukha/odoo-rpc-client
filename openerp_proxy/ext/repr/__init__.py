""" This module provides additional representation capabilities
of RecordList class, like representation as HTML table with
ability to highlight specific rows, which is useful when
used inside IPython notebook

"""

# TODO: rename to IPython or something like that
import os
import six
import os.path
from IPython.display import HTML, FileLink

from ... import (Client,
                 Session)
from ...orm import (RecordList,
                    Record,
                    Object)
from ...service.report import (Report,
                               ReportResult,
                               ReportService)
from ...service.object import ObjectService

from ...utils import ustr as _
from ...utils import AttrDict

from .utils import *
from .generic import *


class RecordListData(RecordList):
    """ Extend record list to add aditional methods related to RecordList representation
    """

    def as_table(self, *fields):
        """ Table representation of record list

            (Similar to .as_html_table method, but for console
             for table generation uses class 'BaseTable', which is base class
             for HTMLTable)

            All arguments passed are fields to be displayed
        """
        return self.as_html_table(*fields)

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
            "Client": self.object.client.get_url(),
            "Record count": self.length,
        }, caption=_(self), help=help_text)


class HTMLRecord(Record):
    """ Adds HTML representation of record
    """

    def get_table_data(self, *fields):
        """ Returns list of lists representation of two-columns table (Field name, Field Value)

            :return: list of lists
        """
        if not fields:
            fields = sorted((HField(col_name, name=col_data['string'])
                             for col_name, col_data in self._columns_info.items()
                             if col_name in self._object.simple_fields),
                            key=lambda x: _(x))

        # Convert all fields to HField instances
        parsed_fields = [toHField(field) for field in fields]

        # Prefetch available fields
        to_prefetch = [f._field
                       for f in parsed_fields
                       if isinstance(f._field, six.string_types)]
        self._lcache.prefetch_fields(to_prefetch)

        return [(field, field(self))
                for field in parsed_fields]

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
        html_data = dict(self.get_table_data(*fields))

        return HTML(describe_object_html(html_data,
                                         _("Record: %s") % self._name,
                                         help=_("Data for %s") % self._name))

    def as_table(self, *fields):
        """ Returns text table representation of this Record.
            By default show all record fields.
            all passed positional arguments are treated as field names to be displayed.
            all positional arguments must be of types supported by toHField method
            (it is used to convert them to HField instances)

           :param list fields: list of fields to display in table representation
        """
        return PrettyTable(self.get_table_data(*fields),
                           headers=[u'Field', u'Value'])

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
            "Client": self._object.client.get_url(),
            "ID": self.id,
            "Name": self._name,
        }, caption=_(self._name), help=help_text)


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
                HField('name', name='Name', silent=True),
                HField('info.string', name='Disp. Name', silent=True),
                HField('info.type', name='Type', silent=True),
                HField('info.required', name='Required', silent=True),
                HField('info.help', name='Help', silent=True),
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
        return HTMLTable(info_struct,
                         fields,
                         caption=u'Fields for %s' % _(self._object.name),
                         display_help=False)

    @property
    def html_table(self):
        """ HTML Table representation of columns info
        """
        if self._html_table is None:
            self._html_table = self.as_html_table()
        return self._html_table

    def _repr_html_(self):
        """ HTML representation for columns info
        """
        return self.html_table._repr_html_()

    def _repr_pretty_(self, printer, cycle):
        """ Pretty representation of columns info
        """
        return self.html_table._repr_pretty_(printer, cycle)


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
            "Client": self.client.get_url(),
            "Model": self.model.model,
            "Record count": self.search([], count=True),
        }, caption=_(self.model.name), help=help_text)


class ClientRegistedObjects(list):
    """ Simple class make registered objects be displayed as HTML table
    """
    def __init__(self, service, *args, **kwargs):
        super(ClientRegistedObjects, self).__init__(*args, **kwargs)
        self._service = service
        self._html_table = None

    @property
    def html_table(self):
        if self._html_table is None:
            ids = self._service.execute('ir.model', 'search', [('model', 'in', list(self))])
            read = self._service.execute('ir.model', 'read', ids, ['name', 'model', 'info'])
            self._html_table = HTMLTable(read,
                                         (('name', 'Name'),
                                          ('model', 'System Name'),
                                          ('info', 'Description')),
                                         caption='Registered models',
                                         display_help=False)
        return self._html_table

    def _repr_html_(self):
        return self.html_table._repr_html_()


class ObjectServiceHtmlMod(ObjectService):
    """ Simple class to add some HTML display features to ObjectService
    """
    def _get_registered_objects(self):
        res = super(ObjectServiceHtmlMod, self)._get_registered_objects()
        return ClientRegistedObjects(self, res)


class ClientHTML(Client):
    """ HTML modifications for Client class
    """

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (u"To get list of registered objects for thist database<br/>"
                     u"access <i>registered_objects</i> property:<br/>"
                     u"&nbsp;<i>.registered_objects</i><br/>"
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
                         caption=u'Available reports',
                         display_help=False)

    @property
    def html_table(self):
        """ HTML Table representation of reports info
        """
        if self._html_table is None:
            self._html_table = self.as_html_table()
        return self._html_table

    def _repr_html_(self):
        """ HTML representation for reports info
        """
        return self.html_table._repr_html_()

    def _repr_pretty_(self, printer, cycle):
        """ Pretty representation of reports info
        """
        return self.html_table._repr_pretty_(printer, cycle)


class ReportServiceExt(ReportService):
    """ Adds html representation for report service
    """

    def _get_available_reports(self):
        """ Returns list of reports registered in system
        """
        return AvailableReportsInfo(
            super(ReportServiceExt, self)._get_available_reports())

    def _repr_html_(self):
        return (u"<div class='panel panel-default'>"
                u"<div class='panel-heading'>Report Service</div>"
                u"<div class='panel-body'>"
                u"To get list of available reports<br/>"
                u"You can access <i>available_reports</i><br/>"
                u"property of this service: "
                u"<pre>.available_reports</pre>"
                u"</div>"
                u"</div>")


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
        help_text = (u"To get connection just call<br/> <ul>"
                     u"<li>session.<b>aliase</b></li>"
                     u"<li>session[<b>index</b>]</li>"
                     u"<li>session[<b>aliase</b>]</li> "
                     u"<li>session[<b>url</b>]</li>"
                     u"<li>session.get_db(<b>url</b>|<b>index</b>|<b>aliase</b>)</li></ul>")

        data = u"<tr><th>DB URL</th><th>DB Index</th><th>DB Aliases</th></tr>"
        for url in self._databases.keys():
            index = self._index_url(url)
            aliases = u", ".join((_(al) for al, aurl in self.aliases.items() if aurl == url))
            data += tr(td(url), td(index), td(aliases))

        table = TMPL_TABLE % {'styles': '',
                              'extra_classes': 'table-striped',
                              'rows': data}

        return TMPL_INFO_WITH_HELP % {'info': table,
                                      'caption': u"Previous connections",
                                      'help': help_text}

