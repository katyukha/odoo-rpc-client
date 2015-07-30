from . import BaseTestCase
from openerp_proxy.core import Client
from openerp_proxy.orm.record import Record
from openerp_proxy.orm.record import RecordList
from openerp_proxy.exceptions import ConnectorError

try:
    import unittest.mock as mock
except ImportError:
    import mock


import numbers

class Test_20_Object(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.object = self.client.get_obj('res.partner')

    def test_dir(self):
        self.assertIn('read', dir(self.object))
        self.assertIn('search', dir(self.object))
        self.assertIn('write', dir(self.object))
        self.assertIn('unlink', dir(self.object))
        self.assertIn('create', dir(self.object))

        # test if normal mehtods avalilable in dir(object)
        #self.assertIn('search_records', dir(self.object))
        #self.assertIn('browse', dir(self.object))

    def test_getttr(self):
        self.assertEqual(self.object.search.__name__, 'res.partner:search')

        # Test that attibute error is raised on access on private methods
        with self.assertRaises(AttributeError):
            self.object._do_smthing_private

    def test_call_unexistent_method(self):
        # method wrapper will be created
        self.assertEqual(self.object.some_unexisting_mehtod.__name__, 'res.partner:some_unexisting_mehtod')

        # but exception should be raised
        with self.assertRaises(ConnectorError):
            self.object.some_unexisting_mehtod([1])

    def test_model(self):
        self.assertIsInstance(self.object.model, Record)
        self.assertEqual(self.object.name, self.object.model.model)
        self.assertEqual(self.object.model, self.object._model)

        # this will check that model_name is result of name_get on model record
        self.assertEqual(self.object.model_name, self.object.model._name)

    def test_search(self):
        res = self.object.search([('id', '=', 1)])
        self.assertIsInstance(res, list)
        self.assertEqual(res, [1])

        res = self.object.search([('id', '=', 1)], count=1)
        self.assertIsInstance(res, numbers.Integral)
        self.assertEqual(res, 1)

    def test_search_records(self):
        res = self.object.search_records([('id', '=', 1)])
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, 1)
        self.assertEqual(res[0].id, 1)

        res = self.object.search_records([('id', '=', 99999)])
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, 0)

        res = self.object.search_records([('id', '=', 1)], count=1)
        self.assertIsInstance(res, numbers.Integral)
        self.assertEqual(res, 1)

    def test_read_records(self):
        # read one record
        res = self.object.read_records(1)
        self.assertIsInstance(res, Record)
        self.assertEqual(res.id, 1)

        # read set of records
        res = self.object.read_records([1])
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, 1)
        self.assertEqual(res[0].id, 1)

        # try to call read_records with bad argument
        with self.assertRaises(ValueError):
            self.object.read_records(None)

    def test_browse(self):
        with mock.patch.object(self.object, 'read_records') as fake_read_records:
            self.object.browse(1)
            fake_read_records.assert_called_with(1)

        with mock.patch.object(self.object, 'read_records') as fake_read_records:
            self.object.browse([1])
            fake_read_records.assert_called_with([1])

        with mock.patch.object(self.object, 'read_records') as fake_read_records:
            self.object.browse(None)
            fake_read_records.assert_called_with(None)


class Test_21_Record(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.object = self.client.get_obj('res.partner')
        self.record = self.object.browse(1)

    def test_dir(self):
        self.assertIn('read', dir(self.record))
        self.assertIn('search', dir(self.record))
        self.assertIn('write', dir(self.record))
        self.assertIn('unlink', dir(self.record))

        # test if normal mehtods avalilable in dir(object)
        #self.assertIn('refresh', dir(self.record))

    def test_name_get(self):
        self.assertEqual(self.record._name, self.record.name_get()[0][1])

    def test_record_equal(self):
        rec1 = self.record

        rec_list = self.object.search_records([('id', '=', 1)])
        self.assertIsInstance(rec_list, RecordList)
        self.assertEqual(rec_list.length, 1)

        rec2 = rec_list[0]
        self.assertEqual(rec1, rec2)
        self.assertEqual(rec1.id, rec2.id)
        self.assertEqual(rec1._name, rec2._name)

        # Test that equality with simple integers works
        self.assertEqual(rec1, rec2.id)
        self.assertEqual(rec1.id, rec2)

        self.assertNotEqual(rec1, None)
        self.assertNotEqual(rec1, 2)

    def test_getitem(self):
        self.assertEqual(self.record['id'], self.record.id)
        with self.assertRaises(KeyError):
            self.record['some_unexistent_field']

    def test_getattr(self):
        # Check that, if we try to get unexistent field, result will be method
        # wrapper for object method
        f = self.record.some_unexistent_field
        self.assertTrue(callable(f))

    def test_record_to_int(self):
        self.assertIs(int(self.record), 1)

    def test_record_hash(self):
        self.assertEqual(hash(self.record), hash((self.record._object.name, self.record.id)))

    def test_record_relational_fields(self):
        res = self.record.child_ids  # read data from res.partner:child_ids field

        self.assertIsInstance(res, RecordList)
        self.assertTrue(res.length >= 1)
        self.assertIsInstance(res[0], Record)
        self.assertEqual(res[0]._object.name, 'res.partner')

        # test many2one
        self.assertIsInstance(res[0].parent_id, Record)
        self.assertIsNot(res[0].parent_id, self.record)
        self.assertEqual(res[0].parent_id, self.record)

        # test that empty many2one field is avaluated as False
        self.assertIs(self.record.user_id, False)

        # test that empty x2many field is evaluated as empty RecordList
        self.assertIsInstance(self.record.user_ids, RecordList)
        self.assertEqual(self.record.user_ids.length, 0)


class Test_22_RecordList(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.object = self.client.get_obj('res.partner')
        self.obj_ids = self.object.search([], limit=10)
        self.recordlist = self.object.read_records(self.obj_ids)

    def test_ids(self):
        self.assertSequenceEqual(self.recordlist.ids, self.obj_ids)

    def test_length(self):
        self.assertEqual(self.recordlist.length, len(self.obj_ids))
        self.assertEqual(len(self.recordlist), len(self.obj_ids))

    def test_getitem(self):
        id1 = self.obj_ids[0]
        id2 = self.obj_ids[-1]

        id_slice = self.obj_ids[2:15:2]

        self.assertIsInstance(self.recordlist[0], Record)
        self.assertEqual(self.recordlist[0].id, id1)

        self.assertIsInstance(self.recordlist[-1], Record)
        self.assertEqual(self.recordlist[-1].id, id2)

        res = self.recordlist[2:15:2]
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, len(id_slice))
        self.assertSequenceEqual(res.ids, id_slice)

        with self.assertRaises(IndexError):
            self.recordlist[100]

    def test_contains(self):
        rid = self.obj_ids[0]
        rec = self.object.read_records(rid)

        brid = self.object.search([('id', 'not in', self.obj_ids)], limit=1)[0]
        brec = self.object.read_records(brid)

        self.assertIn(rid, self.recordlist)
        self.assertIn(rec, self.recordlist)

        self.assertNotIn(brid, self.recordlist)
        self.assertNotIn(brec, self.recordlist)

        self.assertNotIn(None, self.recordlist)

    def test_prefetch(self):
        # check that cache is only filled with ids
        self.assertEqual(len(self.recordlist._lcache), self.recordlist.length)
        for record in self.recordlist:
            self.assertEqual(len(record._data), 1)
            self.assertEqual(record._data.keys(), ['id'])

        # prefetch
        self.recordlist.prefetch('name')

        self.assertEqual(len(self.recordlist._lcache), self.recordlist.length)
        for record in self.recordlist:
            self.assertEqual(len(record._data), 2)
            self.assertEqual(record._data.keys(), ['id', 'name'])

        # TODO: test prefetch related
