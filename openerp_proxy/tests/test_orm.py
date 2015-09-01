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
import collections


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

        # test search_records with read_fields argument
        res = self.object.search_records([], read_fields=['name', 'country_id'], limit=10)
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, 10)
        self.assertEqual(len(res._lcache), res.length)
        for record in res:
            self.assertEqual(len(record._data), 3)
            self.assertItemsEqual(list(record._data), ['id', 'name', 'country_id'])

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

        # Test read with specified fields
        record = self.object.read_records(1, ['name', 'country_id'])
        self.assertEqual(len(record._data), 3)
        self.assertItemsEqual(list(record._data), ['id', 'name', 'country_id'])

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

    def test_object_equal(self):
        self.assertEqual(self.object, self.client['res.partner'])
        self.assertIs(self.object, self.client['res.partner'])
        self.assertNotEqual(self.object, self.client['res.users'])
        self.assertIsNot(self.object, self.client['res.users'])

    def test_str(self):
        self.assertEqual(str(self.object), u"Object ('res.partner')")

    def test_repr(self):
        self.assertEqual(repr(self.object), str(self.object))


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

    def test_proxy_property(self):
        self.assertIs(self.record._proxy, self.client)
        self.assertIs(self.record._object.proxy, self.client)
        self.assertIs(self.object.proxy, self.client)

    def test_as_dict(self):
        rdict = self.record.as_dict

        self.assertIsInstance(rdict, dict)
        self.assertIsNot(rdict, self.record._data)
        self.assertItemsEqual(rdict, self.record._data)

        # test that changes to rdict will not calue changes to record's data
        rdict['new_key'] = 'new value'

        self.assertIn('new_key', rdict)
        self.assertNotIn('new_key', self.record._data)

    def test_str(self):
        self.assertEqual(str(self.record), u"R(res.partner, 1)[%s]" % (self.record.name_get()[0][1]))

    def test_repr(self):
        self.assertEqual(str(self.record), repr(self.record))

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

    def test_record_refresh(self):
        # read all data for record
        self.record.read()

        # read company_id field
        self.record.company_id.name

        # check that data had been loaded
        self.assertTrue(len(self.record._data.keys()) > 5)

        # test before refresh
        self.assertEqual(len(self.record._cache.keys()), 2)
        self.assertIn('res.partner', self.record._cache)
        self.assertIn('res.company', self.record._cache)
        self.assertIn(len(list(self.record._cache['res.company'].values())[0]), [2, 3])
        self.assertIn('name', list(self.record._cache['res.company'].values())[0])

        # refresh record
        self.record.refresh()

        # test after refresh
        self.assertEqual(len(self.record._data.keys()), 1)
        self.assertItemsEqual(list(self.record._data), ['id'])
        self.assertEqual(len(self.record._cache.keys()), 2)
        self.assertIn('res.partner', self.record._cache)
        self.assertIn('res.company', self.record._cache)
        self.assertEqual(len(list(self.record._cache['res.company'].values())[0]), 1)
        self.assertNotIn('name', list(self.record._cache['res.company'].values())[0])


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

    def test_recods(self):
        self.assertIsInstance(self.recordlist.records, list)
        self.assertIsInstance(self.recordlist.records[0], Record)

    def test_str(self):
        self.assertEqual(str(self.recordlist), u"RecordList(res.partner): length=10")

    def test_repr(self):
        self.assertEqual(repr(self.recordlist), str(self.recordlist))

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

    def test_getattr(self):
        with mock.patch.object(self.object, 'some_server_method') as fake_method:
            # bug override in mock object (python 2.7)
            if not getattr(fake_method, '__name__', False):
                fake_method.__name__ = fake_method.name
            self.recordlist.some_server_method('arg1', 'arg2')
            fake_method.assert_called_with(self.recordlist.ids, 'arg1', 'arg2')

    def test_delitem(self):
        r = self.recordlist[5]
        self.assertEqual(len(self.recordlist), 10)

        del self.recordlist[5]

        self.assertEqual(len(self.recordlist), 9)
        self.assertNotIn(r, self.recordlist)

    def test_setitem(self):
        rec = self.object.search_records([('id', 'not in', self.recordlist.ids)], limit=1)[0]

        old_rec = self.recordlist[8]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)
        self.assertIn(old_rec, self.recordlist)

        self.recordlist[8] = rec

        self.assertEqual(len(self.recordlist), 10)
        self.assertIn(rec, self.recordlist)
        self.assertNotIn(old_rec, self.recordlist)

        with self.assertRaises(ValueError):
            self.recordlist[5] = 25

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

    def test_insert_record(self):
        rec = self.object.search_records([('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        self.recordlist.insert(1, rec)

        self.assertEqual(len(self.recordlist), 11)
        self.assertIn(rec, self.recordlist)
        self.assertEqual(self.recordlist[1], rec)

    def test_insert_by_id(self):
        rec = self.object.search_records([('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        self.recordlist.insert(1, rec.id)

        self.assertEqual(len(self.recordlist), 11)
        self.assertIn(rec, self.recordlist)
        self.assertEqual(self.recordlist[1], rec)

    def test_insert_bad_value(self):
        rec = self.object.search_records([('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        with self.assertRaises(AssertionError):
            self.recordlist.insert(1, "some strange type")

    def test_prefetch(self):
        cache = self.recordlist._cache
        lcache = self.recordlist._lcache

        # check that cache is only filled with ids
        self.assertEqual(len(lcache), self.recordlist.length)
        for record in self.recordlist:
            # Note that record._data is a property, which means
            # record._lcache[record.id]. _data property is dictionary.
            self.assertEqual(len(record._data), 1)
            self.assertItemsEqual(list(record._data), ['id'])

        # prefetch normal field
        self.recordlist.prefetch('name')

        self.assertEqual(len(self.recordlist._lcache), self.recordlist.length)
        for record in self.recordlist:
            self.assertEqual(len(record._data), 2)
            self.assertItemsEqual(list(record._data), ['id', 'name'])

        # check that cache contains only res.partner object cache
        self.assertEqual(len(cache), 1)
        self.assertIn('res.partner', cache)
        self.assertNotIn('res.country', cache)

        # prefetch related field name of caountry and country code
        self.recordlist.prefetch('country_id.name', 'country_id.code')

        # test that cache now contains two objects ('res.partner',
        # 'res.country')
        self.assertEqual(len(cache), 2)
        self.assertIn('res.partner', cache)
        self.assertIn('res.country', cache)

        c_cache = cache['res.country']
        country_checked = False  # if in some cases selected partners have no related countries, raise error
        for record in self.recordlist:
            # test that country_id field was added to partner's cache
            self.assertEqual(len(record._data), 3)
            self.assertItemsEqual(list(record._data), ['id', 'name', 'country_id'])

            # if current partner have related country_id
            #
            # Note, here check 'country_id' via '_data' property to avoid lazy
            # loading of data.
            country_id = record._data['country_id']

            # if data is in form [id, <name_get result>]
            if isinstance(country_id, collections.Iterable):
                country_id = country_id[0]
                country_is_list = True

            if country_id:
                country_checked = True

                # test, that there are some data for this country_id in country
                # cache
                self.assertIn(country_id, c_cache)

                # Note that, in case, of related many2one fields, Odoo may
                # return list, with Id and resutlt of name_get method.
                # thus, we program will imediatly cache this value
                if country_is_list:
                    self.assertEqual(len(c_cache[country_id]), 4)
                    self.assertItemsEqual(list(c_cache[country_id]), ['id', 'name', 'code', '__name_get_result'])
                else:
                    self.assertEqual(len(c_cache[country_id]), 4)
                    self.assertItemsEqual(list(c_cache[country_id]), ['id', 'name', 'code', '__name_get_result'])

        self.assertTrue(country_checked, "Country must be checked. may be there are wrong data in test database")

    def test_sorting(self):
        def to_names(rlist):
            return [r.name for r in rlist]

        names = to_names(self.recordlist)

        self.assertSequenceEqual(sorted(names), to_names(sorted(self.recordlist, key=lambda x: x.name)))
        self.assertSequenceEqual(sorted(names, reverse=True), to_names(sorted(self.recordlist, key=lambda x: x.name, reverse=True)))
        self.assertSequenceEqual(list(reversed(names)), to_names(reversed(self.recordlist)))

        # test recordlist sort methods
        rlist = self.recordlist.copy()
        rnames = names[:]  # copy list
        rlist.sort(key=lambda x: x.name)   # inplace sort
        rnames.sort()  # inplace sort
        self.assertSequenceEqual(rnames, to_names(rlist))

        # test recordlist reverse method
        rlist = self.recordlist.copy()
        rnames = names[:]  # copy list
        rlist.reverse()    # inplace reverse
        rnames.reverse()   # inplace reverse
        self.assertSequenceEqual(rnames, to_names(rlist))

    def test_search(self):
        # TODO: test for context
        with mock.patch.object(self.object, 'search') as fake_method:
            self.recordlist.search([('id', '!=', 1)], limit=5)
            fake_method.assert_called_with([('id', 'in', self.recordlist.ids), ('id', '!=', 1)], limit=5)

    def test_search_records(self):
        # TODO: test for context
        with mock.patch.object(self.object, 'search_records') as fake_method:
            self.recordlist.search_records([('id', '!=', 1)], limit=4)
            fake_method.assert_called_with([('id', 'in', self.recordlist.ids), ('id', '!=', 1)], limit=4)

    def test_read(self):
        # TODO: test for context
        #       or remove this test and method, because getattr pass context
        #       too
        with mock.patch.object(self.object, 'read') as fake_method:
            self.recordlist.read(['name'])
            fake_method.assert_called_with(self.recordlist.ids, ['name'])

    def test_filter(self):
        res = self.recordlist.filter(lambda x: x.id % 2 == 0)
        expected_ids = [r.id for r in self.recordlist if r.id % 2 == 0]
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.ids, expected_ids)

    def test_group_by(self):
        res = self.recordlist.group_by(lambda x: x.id % 2 == 0)
        self.assertIsInstance(res, collections.defaultdict)
        self.assertItemsEqual(res.keys(), [True, False])
        # TODO: write better test

        res = self.recordlist.group_by('country_id')
