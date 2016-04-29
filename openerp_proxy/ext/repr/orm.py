import six

from IPython.display import HTML

from ...utils import ustr as _
from ...utils import AttrDict
from ...orm import (RecordList,
                    Record,
                    Object)
from .utils import describe_object_html
from .generic import (HField,
                      toHField,
                      # FieldNotFoundException,
                      # PrettyTable,
                      # BaseTable,
                      HTMLTable)


class RecordListData(RecordList):
    """ Extends record list to add aditional methods
        related to RecordList representation
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

            :param fields: list of fields to display.
                           each field should be string with dot splitted names
                           of related object, or callable of one argument
                           (record instance) or *HField* instance or
                           tuple(field_path|callable, field_name)
            :type fields: list(string | callable | HField | tuple(field, name))
            :param dict highlighters: dictionary in format::

                                          {color: callable(record)->bool}

                                      where *color* any color suitable for HTML
                                      and callable is function of
                                      *Record instance* which decides,
                                      if record should be colored by this color
            :param str caption: String to be used as table caption
            :return: HTMLTable
        """
        if not fields:
            fields = ('id', '_name')

        kwargs['caption'] = kwargs.get('caption',
                                       'RecordList(`%s`)' % self.object.name)
        table = HTMLTable(self, fields, **kwargs)

        # Prefetch available fields
        to_prefetch = (f._field
                       for f in table.fields
                       if isinstance(f._field, six.string_types))
        self._lcache.prefetch_fields(to_prefetch)

        return table

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (
            u"To get table representation of data call method<br/>"
            u"&nbsp;<i>.as_html_table</i><br/>"
            u"passing as arguments fields You want to see in resulting table"
            u"<br/>"
            u"for better information get doc on as_html_table method:<br/>"
            u"&nbsp;<i>.as_html_table?</i><br/>"
            u"example of using this mehtod:<br/>"
            u"&nbsp;<i>.as_html_table('id','name','_name')</i><br/>"
            u"Here <i>_name</i> field is aliase for result of <i>name_get</i> "
            u"method called on record"
        )

        return describe_object_html({
            "Object": self.object,
            "Client": self.object.client.get_url(),
            "Record count": self.length,
        }, caption=_(self), help=help_text)


class HTMLRecord(Record):
    """ Adds HTML representation of record
    """

    def get_table_data(self, *fields):
        """ Returns list of lists representation of three-columns table:
            (Field name, System name, Field Value)

            :return: list of lists
        """
        if not fields:
            # create list of HField instances of simple fields
            fields = sorted((HField(name, name=info['string'])
                             for name, info in self._columns_info.items()
                             if name in self._object.simple_fields),
                            key=lambda x: _(x))

        # Convert all fields to HField instances
        parsed_fields = [toHField(field) for field in fields]

        # Prefetch available fields
        to_prefetch = (f._field
                       for f in parsed_fields
                       if isinstance(f._field, six.string_types))
        self._lcache.prefetch_fields(to_prefetch)

        return [(str(field),
                 field._field if isinstance(field._field,
                                            six.string_types) else '',
                 field(self))
                for field in parsed_fields]

    def as_html(self, *fields):
        """ Returns HTML representation of this Record.
            By default show all record fields.

            All passed positional arguments are treated as field names.
            Also posible to pass dot-separated related fields
            like ('move_dest_id.location_dest_id')
            Type of all positional arguments should be string or HField

            :param list fields: list of field names to display
            :return: ipython's HTML object representing this record
            :rtype: HTML
        """
        return HTMLTable(self.get_table_data(*fields),
                         (HField('0', name='Field name', is_header=True),
                          HField('1', name='System name'),
                          HField('2', name='Value')),
                         caption=_("Record: %s") % self._name)

    def as_table(self, *fields):
        """ Returns text table representation of this Record.
            By default show all record fields.

            All passed positional arguments are treated as field names.
            Also posible to pass dot-separated related fields
            like ('move_dest_id.location_dest_id')
            Type of all positional arguments should be string or HField

            :param list fields: list of fields to display
        """
        return self.as_html(*fields)

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (
            u"To get HTML Table representation of this record call method:"
            u"<br/>"
            u"&nbsp;<i>.as_table()</i><br/>"
            u"Optionaly You can pass list of fields You want to see:<br/>"
            u"&nbsp;<i>.as_table('name', 'origin')</i><br/>"
            u"for better information get doc on <i>as_table</i> method:<br/>"
            u"&nbsp;<i>.as_table?</i><br/>"
        )

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
    """ Modifies object's columns_info to return HTML capable
        representation of fields
    """

    def _get_columns_info(self):
        res = super(ObjectHTML, self)._get_columns_info()
        return ColInfo(self, res)

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (
            u"To get information about columns access property<br/>"
            u"&nbsp;<i>.columns_info</i><br/>"
            u"Also there are available standard server-side methods:<br/>"
            u"&nbsp;<i>search</i>, <i>read</i>, <i>write</i>, <i>unlink</i>"
            u"</br>"
            u"And special methods provided <i>openerp_proxy's orm</i>:"
            u"<ul style='margin-top:1px'>"
            u"<li><i>search_records</i> - same as <i>search</i> but returns "
            u"<i>RecordList</i> instance</li>"
            u"<li><i>read_records</i> - same as <i>read</i> but returns "
            u"<i>Record</i> or <i>RecordList</i> instance</li>"
            u"<ul><br/>")

        return describe_object_html({
            "Name": self.model.name,
            "Client": self.client.get_url(),
            "Model": self.model.model,
            "Record count": self.search([], count=True),
        }, caption=_(self.model.name), help=help_text)
