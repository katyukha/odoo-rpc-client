import os
import six
import csv
import os.path
import tempfile
import tabulate
from IPython.display import FileLink


from ...utils import ustr as _
from ...utils import normalizeSField

from .utils import *


__all__ = ('FieldNotFoundException',
           'HField',
           'toHField',
           'PrettyTable',
           'BaseTable',
           'HTMLTable')


def toHField(field):
    """ Convert value to HField instance

        :param field: value to convert to HField instance. Could be string
                      with dot splitted names of related object, or callable
                      of one argument (record instance) or *HField* instance or
                      tuple(field_path|callable, field_name)
        :return: HField instance based on passed value
        :rtype: HField
    """
    if isinstance(field, HField):
        return field
    elif isinstance(field, six.string_types):
        return HField(field)
    elif callable(field):
        return HField(normalizeSField(field))
    elif isinstance(field, (tuple, list)) and len(field) == 2:
        return HField(field[0], name=field[1])
    else:
        raise ValueError('Unsupported field type: %s' % repr(field))


class FieldNotFoundException(Exception):
    """ Exception raised when HField cannot find field in object been processed
    """
    def __init__(self, obj, name, original_exc=None):
        self.name = name
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
                elif callable(r) and not fields:  # it is last field and it is callable
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

    def __repr__(self):
        return u"<HFiled: %s>" % self


class PrettyTable(object):
    """ Just a simple warapper around tabulate.tabulate to show IPython displayable table

        Only 'pretty' representation, yet.
    """
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    @property
    def table(self):
        return tabulate.tabulate(*self._args, **self._kwargs)

    def _repr_pretty_(self, printer, cycle):
        return printer.text(self.table)


class BaseTable(object):
    """ Base class for table representation

        :param data: record list (or iterable of anything other) to create represetation for
        :type data: RecordList|iterable
        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance) or *HField* instance or
                       tuple(field_path|callable, field_name)
        :type fields: list(str | callable | HField instance | tuple(field, name))
    """
    def __init__(self, data, fields):
        self._data = data
        self._fields = []
        self.update(fields=fields)

    def update(self, fields=None):
        """ This method is used to change BaseTable fields, thus, changing representation

            arguments same as for constructor, except 'data' arg, which is absent in this method

        :param fields: list of fields to display. each field should be string
                       with dot splitted names of related object, or callable
                       of one argument (record instance) or *HField* instance or
                       tuple(field_path|callable, field_name)
        :type fields: list(str | callable | HField instance | tuple(field, name))
        :return: self
        """
        fields = [] if fields is None else fields
        for field in fields:
            self._fields.append(toHField(field))
        return self

    @property
    def fields(self):
        """ List of fields of table.
            :type: list of HField instances
        """
        return self._fields

    @property
    def data(self):
        """ Data, table is based on
        """
        return self._data

    def __iter__(self):
        """ Iterateive structure similar to list of lists
        """
        for record in self.data:
            # Note: yielding here list, becouse attempt to yield
            # smthing like ``yield (f(record) for f in self.fields)`` failed
            yield [field(record) for field in self.fields]

    def to_csv(self):
        """ Write table to CSV file and return FileLink object for it

            :return: instance of FileLink
            :rtype: FileLink
        """
        # Python 2/3 compatability
        if six.PY3:
            adapt = lambda s: _(s)
            fmode = 'wt'
        else:
            fmode = 'wb'
            adapt = lambda s: _(s).encode('utf-8')

        tmp_file = tempfile.NamedTemporaryFile(mode=fmode, dir=CSV_PATH, suffix='.csv', delete=False)
        with tmp_file as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(tuple((adapt(h) for h in self.fields)))
            for row in self:
                csv_writer.writerow(tuple((adapt(val) for val in row)))
        return FileLink(os.path.join(CSV_PATH, os.path.split(tmp_file.name)[-1]))

    def _repr_pretty_(self, printer, cycle):
        return printer.text(PrettyTable(self, headers=self.fields).table)


# TODO: also implement vertical table orientation, which could be usefult for
# comparing few records or reuse same code for displaying single record.
class HTMLTable(BaseTable):
    """ HTML Table representation object for RecordList

        :param data: record list (or iterable of anything other) to create represetation for
        :type data: RecordList|iterable
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
    def __init__(self, data, fields, caption=None, highlighters=None, **kwargs):
        super(HTMLTable, self).__init__(data, fields)
        self._caption = u"HTMLTable"
        self._highlighters = {}

        # Note: Fields already updated by base class
        self.update(caption=caption, highlighters=highlighters, **kwargs)

    def update(self, fields=None, caption=None, highlighters=None, **kwargs):
        """ This method is used to change HTMLTable initial data, thus, changing representation
            Can be used for example, when some function returns partly configured HTMLTable instance,
            but user want's to display more fields for example, or add some custom highlighters

            arguments same as for constructor, except 'data' arg, which is absent in this method

            :return: self
        """
        super(HTMLTable, self).update(fields=fields)
        self._caption = _(self.data) if caption is None else _(caption)

        if highlighters is not None:
            self._highlighters.update(highlighters)

        return self

    @property
    def caption(self):
        """ Table caption
        """
        return self._caption

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
        theaders = u"".join((th(header) for header in self.fields))
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
        for record in self.data:
            hcolor = self.highlight_record(record)
            tdata = u"".join(
                (td(field(record)) for field in self.fields)
            )
            if hcolor:
                data += throw % (hcolor, tdata)
            else:
                data += trow % tdata
        return table % data
