from openerp_proxy.service.service import ServiceBase


class ReportService(ServiceBase):
    """ Service class to simplify interaction with 'report' service
    """
    class Meta:
        name = 'report'

    def report(self, report_name, ids, context):
        """ Proxy to report service *report* method

            @param report_name: string representing name of report service
            @param ids: list of object ID to get report for
            @param context: Ususaly have to have 'model' and 'id' keys that describes object to get report for
            @return: ID of report to get by method *report_get*
        """
        return self._service.report(self._erp_proxy.dbname, self._erp_proxy.uid, self._erp_proxy.pwd, report_name, ids, context)

    def report_get(self, report_id):
        """ Proxy method to report servce *report_get* method

            @param report_id: int that represents ID of report to get
            @return: dictinary with keys:
                        - 'state': boolean, True if report generated correctly
                        - 'result': base64 encoded content of report
                        - 'format': string representing format, report generated in

        """
        return self._service.report_get(self._erp_proxy.dbname, self._erp_proxy.uid, self._erp_proxy.pwd, report_id)
