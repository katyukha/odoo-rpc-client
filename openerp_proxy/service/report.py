from openerp_proxy.service.service import ServiceBase
from extend_me import ExtensibleType

from openerp_proxy.exceptions import Error


class ReportError(Error):
    pass


class ReportResult(object):
    """ Just a simple and extensible wrapper on report result

        As variant of usage - wrap result returned by server methods
        ``report_get`` and ``render_report`` like::
    """
    __metaclass__ = ExtensibleType._('ReportResult')

    def __init__(self, result, path=None):
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
            self._content = base64.decodestring(self.result)
        return self._content

    @property
    def path(self):
        """ Path where file is located or will be located on save
        """
        if self._path is None:
            import hashlib
            content_hash = hashlib.sha256(self.result).hexdigest()
            self._path = content_hash + '.' + self.format
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


class ReportService(ServiceBase):
    """ Service class to simplify interaction with 'report' service
    """
    class Meta:
        name = 'report'

    def _get_available_reports(self):
        """ Returns list of report names registered in system
        """
        report_obj = self.proxy.get_obj('ir.actions.report.xml')
        return list(set((r.report_name for r in report_obj.search_records([]))))

    @property
    def available_reports(self):
        """ Returns list of report names registered in system
        """
        return self._get_available_reports()

    def _prepare_report_data(self, model, ids, report_type):
        """ Performs preparation of data
        """
        ids = [ids] if isinstance(ids, (int, long)) else ids
        return {
            'model': model,
            'id': ids[0],
            'ids': ids,
            'report_type': report_type,
        }

    def report(self, report_name, model, ids, report_type='pdf', context=None):
        """ Proxy to report service *report* method

            :param str report_name: string representing name of report service
            :param str model: name of model to generate report for
            :param ids: list of object ID to get report for (or just single id)
            :type ids: list of int | int
            :param str report_type: Type of report to generate. default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :return: ID of report to get by method *report_get*
            :rtype: int
        """
        context = {} if context is None else context
        ids = [ids] if isinstance(ids, (int, long)) else ids
        data = self._prepare_report_data(model, ids, report_type)
        return self._service.report(self.proxy.dbname,
                                    self.proxy.uid,
                                    self.proxy._pwd,
                                    report_name,
                                    ids,
                                    data,
                                    context)

    def report_get(self, report_id, wrap_result=False):
        """ Proxy method to report service *report_get* method

            :param int report_id: int that represents ID of report to get
                                  (value returned by report method)
            :param bool wrap_result: if set to True, then instead of standard dict,
                                     ReportResult instance will be returned.
                                     default: False
            :return: ReportResult or dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report file
                        - 'format': string representing format, report generated in

                     return type controlled be *wrap_result* parametr
            :rtype: dict|ReportResult
        """
        if wrap_result:
            return ReportResult(self._service.report_get(self.proxy.dbname,
                                                         self.proxy.uid,
                                                         self.proxy._pwd,
                                                         report_id))
        else:
            return self._service.report_get(self.proxy.dbname,
                                            self.proxy.uid,
                                            self.proxy._pwd,
                                            report_id)

    def render_report(self, report_name, model, ids, report_type='pdf', context=None, wrap_result=False):
        """ Proxy to report service *render_report* method

            NOTE: available after version 6.1.

            :param str report_name: string representing name of report service
            :param str model: name of model to generate report for
            :param ids: list of object ID to get report for (or just single id)
            :type ids: list of int | int
            :param str report_type: Type of report to generate. default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :param bool wrap_result: if set to True, then instead of standard dict,
                                     ReportResult instance will be returned.
                                     default: False
            :return: ReportResult or dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report file
                        - 'format': string representing format, report generated in

                     return type controlled be *wrap_result* parametr
            :rtype: dict|ReportResult
        """
        context = {} if context is None else context
        ids = [ids] if isinstance(ids, (int, long)) else ids
        data = self._prepare_report_data(model, ids, report_type)

        if wrap_result:
            return ReportResult(self._service.render_report(self.proxy.dbname,
                                                            self.proxy.uid,
                                                            self.proxy._pwd,
                                                            report_name,
                                                            ids,
                                                            data,
                                                            context))
        else:
            return self._service.render_report(self.proxy.dbname,
                                               self.proxy.uid,
                                               self.proxy._pwd,
                                               report_name,
                                               ids,
                                               data,
                                               context)
