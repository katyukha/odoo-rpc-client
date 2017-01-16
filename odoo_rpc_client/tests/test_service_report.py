import six
import os.path
from pkg_resources import parse_version as V

from . import BaseTestCase
from ..client import Client
from ..service.report import (Report,
                              ReportResult)


class Test_Service_Report(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        if self.client.server_version == V('7.0'):
            self.report_name = 'sale.order'
        else:  # >7.0
            self.report_name = 'sale.report_saleorder'

    def test_available_reports(self):
        all_reports = self.client['ir.actions.report.xml'].search_records([])
        expected_names = all_reports.mapped('report_name')

        self.assertItemsEqual(
            list(self.client.services.report.available_reports.keys()),
            expected_names)

        for report in self.client.services.report.available_reports.values():
            self.assertIsInstance(report, Report)

    def test_contains(self):
        self.assertIn(self.report_name, self.client.services.report)

    def test_getitem(self):
        self.assertIs(
            self.client.services.report.available_reports[self.report_name],
            self.client.services.report[self.report_name])

        with self.assertRaises(KeyError):
            self.client.services.report['some_unexistent_report']

    def test_getattr(self):
        self.assertIs(
            self.client.services.report.available_reports[self.report_name],
            getattr(self.client.services.report, self.report_name))

        with self.assertRaises(AttributeError):
            getattr(self.client.services.report, 'some_unexistent_report')

    def test_report_report_name(self):
        self.assertEqual(
            self.client.services.report[self.report_name].name,
            self.report_name)

    def test_report_generate(self):
        so = self.client['sale.order'].search_records([], limit=1)[0]

        result = self.client.services.report[self.report_name].generate(so)

        self.assertIsInstance(result, ReportResult)
        self.assertTrue(result.state)
        self.assertIsInstance(result.result, six.binary_type)
        self.assertEqual(result.format, 'pdf')
        self.assertIsInstance(result.content, six.binary_type)

        # save to default path
        self.assertFalse(os.path.exists(result.path))
        result.save()
        self.assertTrue(os.path.exists(result.path))

        # save to specified path
        my_path = './my-test-report.pdf'
        self.assertFalse(os.path.exists(my_path))
        result.save(my_path)
        self.assertTrue(os.path.exists(my_path))
