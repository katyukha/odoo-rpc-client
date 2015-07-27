from . import BaseTestCase
from openerp_proxy.core import Client
from openerp_proxy.orm.record import Record
from openerp_proxy.orm.record import RecordList


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

    def test_model(self):
        self.assertIsInstance(self.object.model, Record)
        self.assertEqual(self.object.name, self.object.model.model)
        self.assertEqual(self.object.model, self.object._model)

        # this will check that model_name is result of name_get on model record
        self.assertEqual(self.object.model_name, self.object.model._name)


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

    def test_getitem(self):
        self.assertEqual(self.record['id'], self.record.id)
        with self.assertRaises(KeyError):
            self.record['some_unexistent_field']

    def test_getattr(self):
        # Check that, if we try to get unexistent field, result will be method
        # wrapper for object method
        f = self.record.some_unexistent_field
        self.assertTrue(callable(f))
