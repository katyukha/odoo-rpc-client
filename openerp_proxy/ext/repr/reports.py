"""Report representation extensions
"""
import os
import os.path
from IPython.display import FileLink

from ...service.report import (Report,
                               ReportResult,
                               ReportService)
from ...utils import ustr as _
from ...utils import AttrDict

from .utils import (describe_object_html,
                    REPORTS_PATH)
from .generic import (HField,
                      # toHField,
                      # FieldNotFoundException,
                      # PrettyTable,
                      # BaseTable,
                      HTMLTable)


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
        help_text = (
            u"This is report representation.<br/>"
            u"call <i>generate<i> method to generate new report<br/>"
            u"&nbsp;<i>.generate([1, 2, 3])</i><br/>"
            u"Also <i>generate</i> method can receive <br/>"
            u"RecordList or Record instance as first argument.<br/>"
            u"For more information look in "
            u"<a href='http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.service.html#module-openerp_proxy.service.report'>documentation</a>"   # noqa
        )

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
