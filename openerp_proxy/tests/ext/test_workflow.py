import unittest
import os

from pkg_resources import parse_version as V

try:
    import unittest.mock as mock
except ImportError:
    import mock

from ...tests import BaseTestCase
from ... import Client
from ...orm import (Record,
                    RecordList)


@unittest.skipUnless(os.environ.get('TEST_WITH_EXTENSIONS', False), 'requires extensions enabled')
class Test_32_ExtWorkFlow(BaseTestCase):
    def setUp(self):
        super(Test_32_ExtWorkFlow, self).setUp()

        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)

        if self.client.server_version >= V('9.0'):
            self.skipTest('No workflow tests for Odoo version 9.0')
        self.object = self.client.get_obj('sale.order')
        self.record = self.object.browse(1)
        self.obj_ids = self.object.search([], limit=10)
        self.recordlist = self.object.read_records(self.obj_ids)

        self.object_no_wkf = self.client.get_obj('res.partner')
        self.record_no_wkf = self.object_no_wkf.browse(1)
        self.obj_ids_no_wkf = self.object_no_wkf.search([], limit=10)
        self.recordlist_no_wkf = self.object_no_wkf.read_records(self.obj_ids_no_wkf)

    def test_obj_workflow(self):
        res = self.object.workflow
        self.assertIsInstance(res, Record)
        self.assertEqual(res._object.name, 'workflow')
        self.assertEqual(res.osv, 'sale.order')

        res = self.object_no_wkf.workflow
        self.assertIsInstance(res, bool)
        self.assertIs(res, False)

    def test_record_wkf_instance(self):
        res = self.record.workflow_instance
        self.assertIsInstance(res, Record)
        self.assertEqual(res.wkf_id.id, self.object.workflow.id)
        self.assertEqual(res.res_id, self.record.id)

        res = self.record_no_wkf.workflow_instance
        self.assertIsInstance(res, bool)
        self.assertIs(res, False)

    def test_record_wkf_items(self):
        res = self.record.workflow_items
        self.assertIsInstance(res, RecordList)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]._object.name, 'workflow.workitem')

        res = self.record_no_wkf.workflow_items
        self.assertIsInstance(res, list)
        self.assertEqual(res, [])

    @unittest.skipIf(os.environ.get('TEST_WITHOUT_DB_CHANGES', False), 'db changes not allowed. skipped')
    def test_record_signal_send(self):
        # first sale order seems to be in draft state on just created DB
        so = self.record

        # get current SO activity
        act = so.workflow_items[0].act_id
        act_id = act.id

        # get first avalable transition with signal
        trans = [t for t in act.out_transitions if t.signal]
        if not trans:
            raise unittest.SkipTest("There is no avalable transitions in first sale order to test workflow")
        trans = trans[0]

        # send signal
        so.workflow_signal(trans.signal)
        so.refresh()  # refresh record to reflect database changes

        # test it
        self.assertNotEqual(so.workflow_items[0].act_id.id, act_id)
