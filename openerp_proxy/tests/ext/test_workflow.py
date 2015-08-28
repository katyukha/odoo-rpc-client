import unittest
import os

try:
    import unittest.mock as mock
except ImportError:
    import mock

from openerp_proxy.tests import BaseTestCase
from openerp_proxy.core import Client
from openerp_proxy.orm.record import (Record,
                                      RecordList)
from openerp_proxy.orm.object import Object


@unittest.skipUnless(os.environ.get('TEST_WITH_EXTENSIONS', False), 'requires tests enabled')
class Test_32_ExtWorkFlow(BaseTestCase):
    def setUp(self):
        super(Test_32_ExtWorkFlow, self).setUp()

        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.object = self.client.get_obj('sale.order')
        self.record = self.object.browse(1)
        self.obj_ids = self.object.search([], limit=10)
        self.recordlist = self.object.read_records(self.obj_ids)

    def test_obj_workflow(self):
        res = self.object.workflow
        self.assertIsInstance(res, Record)
        self.assertEqual(res._object.name, 'workflow')
        self.assertEqual(res.osv, 'sale.order')

    def test_record_wkf_instance(self):
        res = self.record.workflow_instance
        self.assertIsInstance(res, Record)
        self.assertEqual(res.wkf_id.id, self.object.workflow.id)
        self.assertEqual(res.res_id, self.record.id)

    def test_record_wkf_items(self):
        res = self.record.workflow_items
        self.assertIsInstance(res, RecordList)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]._object.name, 'workflow.workitem')

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
