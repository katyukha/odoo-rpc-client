from openerp_proxy.service.service import ServiceBase


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
        return self._service.report(self.proxy.dbname, self.proxy.uid, self.proxy._pwd, report_name, ids, data, context)

    def report_get(self, report_id):
        """ Proxy method to report service *report_get* method

            :param int report_id: int that represents ID of report to get
                                  (value returned by report method)
            :return: dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report file
                        - 'format': string representing format, report generated in
            :rtype: dict
        """
        return self._service.report_get(self.proxy.dbname, self.proxy.uid, self.proxy._pwd, report_id)

    def render_report(self, report_name, model, ids, report_type='pdf', context=None):
        """ Proxy to report service *render_report* method

            NOTE: available after version 6.1.

            :param str report_name: string representing name of report service
            :param str model: name of model to generate report for
            :param ids: list of object ID to get report for (or just single id)
            :type ids: list of int | int
            :param str report_type: Type of report to generate. default is 'pdf'.
            :param dict context: Aditional info. Optional.
            :return: dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report file
                        - 'format': string representing format, report generated in
            :rtype: dict
        """
        context = {} if context is None else context
        ids = [ids] if isinstance(ids, (int, long)) else ids
        data = self._prepare_report_data(model, ids, report_type)

        return self._service.render_report(self.proxy.dbname, self.proxy.uid, self.proxy._pwd, report_name, ids, data, context)
