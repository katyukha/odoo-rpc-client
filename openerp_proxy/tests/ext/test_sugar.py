import unittest
import os

try:
    import unittest.mock as mock
except ImportError:
    import mock

from .. import BaseTestCase
from ... import Client
from ...orm import (Record,
                    RecordList,
                    Object)


@unittest.skipUnless(os.environ.get('TEST_WITH_EXTENSIONS', False), 'requires extensions enabled')
class Test_31_ExtSugar(BaseTestCase):
    def setUp(self):
        super(Test_31_ExtSugar, self).setUp()

        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.object = self.client.get_obj('res.partner')
        self.record = self.object.browse(1)
        self.obj_ids = self.object.search([], limit=10)
        self.recordlist = self.object.read_records(self.obj_ids)

    def test_obj_search_record(self):
        res = self.object.search_record([('name', 'ilike', 'admin')])
        self.assertIsInstance(res, Record)
        self.assertEqual(res.name, 'Administrator')

    def test_obj_getitem(self):
        res = self.object[self.record.id]
        self.assertIsInstance(res, Record)
        self.assertEqual(res, self.record)

        with self.assertRaises(KeyError):
            self.object['bad key']

    def test_obj_len(self):
        self.assertEqual(len(self.object), self.object.search([], count=True))

    def test_obj_call_name_search(self):
        res = self.object('admin')  # name_search by name. only one record with this name
        self.assertIsInstance(res, Record)
        self.assertEqual(res._name, 'Administrator')

        res = self.object('Bank')
        self.assertIsInstance(res, RecordList)
        bank_ids = [i for i, _ in self.object.name_search('Bank')]
        self.assertItemsEqual(res.ids, bank_ids)

    def test_obj_call_search_records(self):
        with mock.patch.object(self.object, 'search_records') as fake_search_records:
            self.object([('name', 'ilike', 'admin')])
            fake_search_records.assert_called_with([('name', 'ilike', 'admin')])

            self.object([('name', 'ilike', 'admin')], count=True)
            fake_search_records.assert_called_with([('name', 'ilike', 'admin')], count=True)

            self.object(name='admin')
            fake_search_records.assert_called_with([('name', '=', 'admin')])

            self.object()
            fake_search_records.assert_called_with([])

    def test_client_dir(self):
        # test if models are in dir
        self.assertIn('_res_partner', dir(self.client))

        # test if normal methods are listed in dir(client)
        self.assertIn('execute', dir(self.client))

        # test if plugins are listed in dir(client)
        self.assertIn('Test', dir(self.client))

    def test_client_getattr(self):
        res = self.client._res_partner
        self.assertIsInstance(res, Object)
        self.assertEqual(res, self.object)

        with self.assertRaises(AttributeError):
            self.client._some_bad_model

    def test_client_getattr_pluigns(self):
        self.assertEqual(self.client.Test, self.client.plugins.Test)

