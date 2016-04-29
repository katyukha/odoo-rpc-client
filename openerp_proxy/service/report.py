""" Report printing logic

Best way to generate report is::

    data_records = db['res.partner'].search_records([], limit=10)
    report = db.services.report['res.partner'].generate(data_records)
    report.content

where *report* is instance of *ReportResult* and *report.content*
returns already *base64* decoded content of report,
which could be directly written to file (or
just use *report.save(path)* method)
"""

import time
import numbers
from pkg_resources import parse_version
from extend_me import Extensible

from .service import ServiceBase
from ..orm import (Record,
                   RecordList)

from ..exceptions import ReportError


class ReportResult(Extensible):
    """ Just a simple and extensible wrapper on report result

        As variant of usage - wrap result returned by server methods
        ``report_get`` and ``render_report`` like::

            ReportResult(report_get(report_id))

    """

    def __init__(self, report, result, path=None):
        self._report = report
        self._orig_result = result
        self._state = result.get('state', False)
        self._result = result.get('result', None)
        self._format = result.get('format', None)
        self._content = None
        self._path = path

    @property
    def state(self):
        """ Result status. only if True, other fields are available
        """
        return self._state

    @property
    def result(self):
        """ Base64-encoded report content.
            To get already decoded report content, use ``.content`` property

            :raises ReportError: When .state property is False.
                                 This may appear in case when report
                                 is not ready yet, when using
                                 *report* and *report_get* methods
        """
        if self.state is False:
            raise ReportError("Report seems to be not ready yet")
        return self._result

    @property
    def format(self):
        """ Report format
        """
        return self._format

    @property
    def content(self):
        """ Report file content. Already base64-decoded
        """
        if self._content is None:
            import base64
            self._content = base64.b64decode(self.result.encode('utf-8'))
        return self._content

    @property
    def path(self):
        """ Path where file is located or will be located on save
        """
        if self._path is None:
            import hashlib
            content_hash = hashlib.sha256(self.content)
            content_hash = content_hash.hexdigest().encode('utf-8')
            report_name_base = self._report.report_action.name.encode('utf-8')
            report_name_base = report_name_base.replace(b'/', b'-')\
                                               .replace(b':', b'-')
            self._path = str(report_name_base +
                             content_hash +
                             b'.' + self.format.encode('utf-8'))
        return self._path

    def save(self, path=None):
        """ Save's file by specified path or if no path specified
            save it in temp dir with automaticly generated name.
        """
        if path is not None:
            self._path = path
        with open(self.path, 'wb') as f:
            f.write(self.content)
        return self


class Report(Extensible):
    """ Class that represents report.

        useful to simplify report generation

        :param ReportService service: instance of report service
                                      to bind report to
        :param Record report: model of report action

    """

    def __init__(self, service, report):
        self._service = service
        self._report = report

    @property
    def service(self):
        """ Service this report is binded to
        """
        return self._service

    @property
    def report_action(self):
        """ Action of this report
        """
        return self._report

    @property
    def name(self):
        """ Name of report
        """
        return self.report_action.report_name

    def generate(self, model_data, report_type='pdf', context=None):
        """ Generate report

            :param report_data: RecordList or Record or list of obj_ids.
                                represent document or documents
                                to generate report for
            :param str report_type: Type of report to generate.
                                    default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :raises: ReportError
            :return: ReportResult instance that contains generated report
            :rtype: ReportResult
        """
        return self.service.generate_report(self.name,
                                            model_data,
                                            report_type=report_type,
                                            context=context)


class ReportService(ServiceBase):
    """ Service class to simplify interaction with 'report' service
    """
    class Meta:
        name = 'report'

    def __init__(self, *args, **kwargs):
        super(ReportService, self).__init__(*args, **kwargs)
        self._reports = None

    def _get_available_reports(self):
        """ Returns list of reports registered in system
        """
        report_obj = self.client.get_obj('ir.actions.report.xml')
        return {r.report_name: Report(self, r)
                for r in report_obj.search_records([])}

    @property
    def available_reports(self):
        """ Returns dictionary with all available reports

            {<report name> : <Report instance>}
        """
        if self._reports is None:
            self._reports = self._get_available_reports()
        return self._reports

    def _prepare_report_data(self, model, ids, report_type):
        """ Performs preparation of data
        """
        ids = [ids] if isinstance(ids, numbers.Integral) else ids
        return {
            'model': model,
            'id': ids[0],
            'ids': ids,
            'report_type': report_type,
        }

    def __getitem__(self, name):
        return self.available_reports[name]

    def __getattr__(self, name):
        try:
            res = self[name]
        except KeyError as exc:
            raise AttributeError(str(exc))
        return res

    def __contains__(self, report):
        return report in self.available_reports

    def report(self, report_name, model, ids, report_type='pdf', context=None):
        """ Proxy to report service *report* method

            :param str report_name: string representing name of report service
            :param str model: name of model to generate report for
            :param ids: list of object ID to get report for (or just single id)
            :type ids: list of int | int
            :param str report_type: Type of report to generate.
                                    default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :return: ID of report to get by method *report_get*
            :rtype: int
        """
        context = {} if context is None else context
        ids = [ids] if isinstance(ids, numbers.Integral) else ids
        data = self._prepare_report_data(model, ids, report_type)
        return self._service.report(self.client.dbname,
                                    self.client.uid,
                                    self.client._pwd,
                                    report_name,
                                    ids,
                                    data,
                                    context)

    def report_get(self, report_id):
        """ Proxy method to report service *report_get* method

            :param int report_id: int that represents ID of report to get
                                  (value returned by report method)
            :return: dictinary with keys:

                     - 'state': boolean, True if report generated correctly
                     - 'result': base64 encoded content of report file
                     - 'format': string representing format,
                       report generated in

            :rtype: dict
        """
        return self._service.report_get(self.client.dbname,
                                        self.client.uid,
                                        self.client._pwd,
                                        report_id)

    def render_report(self, report_name, model, ids, report_type='pdf',
                      context=None):
        """ Proxy to report service *render_report* method

            NOTE: available after version 6.1.

            :param str report_name: string representing name of report service
            :param str model: name of model to generate report for
            :param ids: list of object ID to get report for (or just single id)
            :type ids: list of int | int
            :param str report_type: Type of report to generate.
                                    default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :return: dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report file
                        - 'format': string representing report format

            :rtype: dict
        """
        context = {} if context is None else context
        ids = [ids] if isinstance(ids, numbers.Integral) else ids
        data = self._prepare_report_data(model, ids, report_type)

        return self._service.render_report(self.client.dbname,
                                           self.client.uid,
                                           self.client._pwd,
                                           report_name,
                                           ids,
                                           data,
                                           context)

    def generate_report(self, report_name, report_data, report_type='pdf',
                        context=None):
        """ Generate specified report for specifed report data.
            Report data could be RecordList or Record instance.
            Result is wrapped into ReportResult class


            :param str report_name: string representing name of report service
            :param report_data: RecordList or Record or ('model_name', obj_ids)
                                represent document or documents
                                to generate report for
            :param str report_type: Type of report to generate.
                                    default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :raises: ReportError
            :return: ReportResult instance that contains generated report
            :rtype: ReportResult
        """
        if isinstance(report_data, RecordList):
            obj_ids = report_data.ids
        elif isinstance(report_data, Record):
            obj_ids = [report_data.id]
        else:  # report_data is list of object ids
            obj_ids = report_data

        report_model = self[report_name].report_action.model

        if self.client.server_version >= parse_version('6.1'):
            report_result = self.render_report(report_name,
                                               report_model,
                                               obj_ids,
                                               report_type=report_type,
                                               context=context)
        else:  # pragma: no cover
            # server < 6.1
            report_id = self.report(report_name,
                                    report_model,
                                    obj_ids,
                                    report_type=report_type,
                                    context=context)
            attempt = 0
            while True:
                report_result = self.report_get(report_id)
                if report_result['state']:
                    break
                else:
                    time.sleep(1)
                    attempt += 1

                if attempt > 200:
                    raise ReportError("Report download timeout!")

        return ReportResult(self.available_reports[report_name],
                            report_result)
