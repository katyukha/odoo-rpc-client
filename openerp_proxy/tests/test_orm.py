import six
import numbers
import collections

from . import (BaseTestCase,
               mock)
from ..core import Client
from ..orm.record import (Record,
                          RecordList,
                          get_record_list)
from ..orm.cache import (empty_cache,
                         ObjectCache,
                         Cache)
from ..orm.object import Object
from ..exceptions import ConnectorError


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
        self.assertIn('search_records', dir(self.object))
        self.assertIn('browse', dir(self.object))

    def test_getttr(self):
        self.assertEqual(self.object.search.__name__, 'search')

        self.assertEqual(self.object.some_partner_method.__name__,
                         '%s:some_partner_method' % self.object.name)
        self.assertTrue(self.object.some_partner_method.__x_stdcall__)

        # Test that attibute error is raised on access on private methods
        with self.assertRaises(AttributeError):
            self.object._do_smthing_private

    def test_call_unexistent_method(self):
        # method wrapper will be created
        self.assertEqual(self.object.some_unexisting_mehtod.__name__,
                         'res.partner:some_unexisting_mehtod')

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
        res = self.object.search_records([],
                                         read_fields=['name', 'country_id'],
                                         limit=10)
        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.length, 10)
        self.assertEqual(len(res._lcache), res.length)
        for record in res:
            self.assertEqual(len(record._data), 3)
            self.assertItemsEqual(list(record._data),
                                  ['id', 'name', 'country_id'])

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
        record = self.object.read_records(1,
                                          ['name', 'country_id'])
        self.assertEqual(len(record._data), 3)
        self.assertItemsEqual(list(record._data),
                              ['id', 'name', 'country_id'])

    def test_browse(self):
        with mock.patch.object(self.object,
                               'read_records') as fake_read_records:
            self.object.browse(1)
            fake_read_records.assert_called_with(1)

        with mock.patch.object(self.object,
                               'read_records') as fake_read_records:
            self.object.browse([1])
            fake_read_records.assert_called_with([1])

        with mock.patch.object(self.object,
                               'read_records') as fake_read_records:
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

    def test_object_specific_extension(self):
        class MyProductObject(Object):

            class Meta:
                name = 'res.users'

            def test_previously_unexistent_method(self):
                return "Method Ok"

        # reload client caches
        self.client.clean_caches()

        # Newly defined object method must be present in res.users model
        res = self.client['res.users'].test_previously_unexistent_method()
        self.assertEqual(res, "Method Ok")

        # but must not be present in other objects / models
        with self.assertRaises(ConnectorError):
            self.client['res.partner'].test_previously_unexistent_method()

    def test_create_write_unlink(self):
        new_partner_id = self.object.create({'name': 'New Partner'})

        self.assertIsInstance(new_partner_id, int)

        self.object.write([new_partner_id], {'name': 'New Partner Name'})

        new_name = self.object.read(new_partner_id, ['name'])['name']

        self.assertEqual(new_name, 'New Partner Name')

        self.assertEqual(self.object.search([('id', '=', new_partner_id)],
                                            count=True),
                         1)
        self.object.unlink([new_partner_id])
        self.assertEqual(self.object.search([('id', '=', new_partner_id)],
                                            count=True),
                         0)


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
        self.assertIn('write', dir(self.record))
        self.assertIn('unlink', dir(self.record))

        # test if normal mehtods avalilable in dir(object)
        self.assertIn('refresh', dir(self.record))

    def test_client_property(self):
        self.assertIs(self.record._client, self.client)
        self.assertIs(self.record._object.client, self.client)
        self.assertIs(self.object.client, self.client)

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
        self.assertEqual(str(self.record),
                         u"R(res.partner, 1)[%s]"
                         u"" % (self.record.name_get()[0][1]))

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
        self.assertEqual(hash(self.record),
                         hash((self.record._object.name, self.record.id)))

    def test_record_relational_fields(self):
        # read data from res.partner:child_ids field
        res = self.record.child_ids

        self.assertIsInstance(res, RecordList)
        self.assertGreaterEqual(res.length, 1)
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
        self.assertGreater(len(self.record._data.keys()), 5)

        # test before refresh
        self.assertEqual(len(self.record._cache.keys()), 2)
        self.assertIn('res.partner', self.record._cache)
        self.assertIn('res.company', self.record._cache)
        self.assertIn(
            len(list(self.record._cache['res.company'].values())[0]), [2, 3])
        self.assertIn(
            'name',
            list(
                self.record._cache['res.company'].values())[0])

        # refresh record
        self.record.refresh()

        # test after refresh
        self.assertEqual(len(self.record._data.keys()), 1)
        self.assertItemsEqual(list(self.record._data), ['id'])
        self.assertEqual(len(self.record._cache.keys()), 2)
        self.assertIn('res.partner', self.record._cache)
        self.assertIn('res.company', self.record._cache)
        self.assertEqual(
            len(list(self.record._cache['res.company'].values())[0]), 1)
        self.assertNotIn(
            'name',
            list(
                self.record._cache['res.company'].values())[0])

    def test_record_specific_extension(self):
        class MyProductRecord(Record):

            class Meta:
                object_name = 'res.users'

            def test_previously_unexistent_record_method(self):
                return "Method Ok Record %s" % self.id

        # Product records must have this method
        user = self.client['res.users'].search_records([], limit=1)[0]
        res = user.test_previously_unexistent_record_method()
        self.assertEqual(res, "Method Ok Record %s" % user.id)

        # other records must not have it
        r = self.client['res.partner'].search_records([], limit=1)[0]
        with self.assertRaises(ConnectorError):
            r.test_previously_unexistent_record_method()

    def test_copy(self):
        res = self.record.copy()

        self.assertIsInstance(res, Record)
        self.assertNotEqual(res.id, self.record.id)

        res = self.record.copy(default={'ref': 'My Test Copy Partner Ref'})
        self.assertIsInstance(res, Record)
        self.assertNotEqual(res.id, self.record.id)
        self.assertNotEqual(res.ref, self.record.ref)
        self.assertEqual(res.ref, 'My Test Copy Partner Ref')


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

    def test_dir(self):
        self.assertIn('read', dir(self.recordlist))
        self.assertIn('write', dir(self.recordlist))
        self.assertIn('unlink', dir(self.recordlist))

        # test if normal mehtods avalilable in dir(object)
        self.assertIn('refresh', dir(self.recordlist))

    def test_ids(self):
        self.assertSequenceEqual(self.recordlist.ids, self.obj_ids)

    def test_length(self):
        self.assertEqual(self.recordlist.length, len(self.obj_ids))
        self.assertEqual(len(self.recordlist), len(self.obj_ids))

    def test_recods(self):
        self.assertIsInstance(self.recordlist.records, list)
        self.assertIsInstance(self.recordlist.records[0], Record)

    def test_str(self):
        self.assertEqual(
            str(self.recordlist), u"RecordList(res.partner): length=10")

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
        with mock.patch.object(self.object,
                               'some_server_method') as fake_method:
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
        rec = self.object.search_records(
            [('id', 'not in', self.recordlist.ids)], limit=1)[0]

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
        rec = self.object.search_records(
            [('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        self.recordlist.insert(1, rec)

        self.assertEqual(len(self.recordlist), 11)
        self.assertIn(rec, self.recordlist)
        self.assertEqual(self.recordlist[1], rec)

    def test_insert_by_id(self):
        rec = self.object.search_records(
            [('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        self.recordlist.insert(1, rec.id)

        self.assertEqual(len(self.recordlist), 11)
        self.assertIn(rec, self.recordlist)
        self.assertEqual(self.recordlist[1], rec)

    def test_insert_bad_value(self):
        rec = self.object.search_records(
            [('id', 'not in', self.recordlist.ids)], limit=1)[0]

        self.assertEqual(len(self.recordlist), 10)
        self.assertNotIn(rec, self.recordlist)

        with self.assertRaises(AssertionError):
            self.recordlist.insert(1, "some strange type")

    def test_mapped_1_simple_field(self):
        res = self.recordlist.mapped('name')
        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], six.string_types)
        self.assertEqual(len(res), len(set(p.name for p in self.recordlist)))

    def test_mapped_2_m2o_field(self):
        res = self.recordlist.mapped('parent_id')
        self.assertIsInstance(res, RecordList)
        self.assertIsInstance(res[0], Record)

        # TODO: rewrite this to test that items was uniquifyed
        self.assertEqual(
            len(res),
            len(set([r.parent_id for r in self.recordlist if r.parent_id])))

    def test_mapped_3_m2o_dot_char_field(self):
        res = self.recordlist.mapped('parent_id.name')
        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], six.string_types)

        # TODO: rewrite this to test that items was uniquifyed
        self.assertEqual(
            len(res),
            len(set([r.parent_id.name
                     for r in self.recordlist if r.parent_id])))

    def test_mapped_4_m2o_dot_char_field(self):
        res = self.recordlist.mapped('country_id.code')
        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], six.string_types)

        # TODO: rewrite this to test that items was uniquifyed
        self.assertEqual(
            len(res),
            len(set([r.country_id.code
                     for r in self.recordlist if r.country_id])))

    def test_mapped_5_m2o_dot_o2m_field(self):
        res = self.recordlist.mapped('user_ids')
        self.assertIsInstance(res, RecordList)
        self.assertIsInstance(res[0], Record)
        self.assertEqual(res[0]._object.name, 'res.users')
        # TODO: implement some additional checks

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
        # if in some cases selected partners have no related countries, raise
        # error
        country_checked = False
        for record in self.recordlist:
            # test that country_id field was added to partner's cache
            self.assertEqual(len(record._data), 3)
            self.assertItemsEqual(
                list(record._data),
                ['id', 'name', 'country_id'])

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
                    self.assertItemsEqual(
                        list(c_cache[country_id]),
                        ['id', 'name', 'code', '__name_get_result'])
                else:
                    self.assertEqual(len(c_cache[country_id]), 4)
                    self.assertItemsEqual(
                        list(c_cache[country_id]),
                        ['id', 'name', 'code', '__name_get_result'])

        self.assertTrue(
            country_checked,
            "Country must be checked. "
            "may be there are wrong data in test database")

    def test_copy(self):
        # test that cipied list and original list have same cache instance,
        # when new_cache arg is set to default value False
        clist = self.recordlist.copy()
        self.assertIs(clist._cache, self.recordlist._cache)

        # When new_cache arg set to True, then new_automaticaly generated cache
        # will be used
        clist = self.recordlist.copy(new_cache=True)
        self.assertIsNot(clist._cache, self.recordlist._cache)

        # test when Cache instance passed to new_cache argument
        cache = Cache(self.recordlist.object.client)
        clist = self.recordlist.copy(new_cache=cache)
        self.assertIs(clist._cache, cache)

        # Test that with wrong argument copy will raise
        with self.assertRaises(ValueError):
            self.recordlist.copy(new_cache=25)

    def test_sorting(self):
        def to_names(rlist):
            """ Convert recordlist to list of names
            """
            return [r.name for r in rlist]

        names = to_names(self.recordlist)

        self.assertSequenceEqual(sorted(names),
                                 to_names(sorted(self.recordlist,
                                                 key=lambda x: x.name)))
        self.assertSequenceEqual(sorted(names, reverse=True),
                                 to_names(sorted(self.recordlist,
                                                 key=lambda x: x.name,
                                                 reverse=True)))
        self.assertSequenceEqual(list(reversed(names)),
                                 to_names(reversed(self.recordlist)))

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
            fake_method.assert_called_with(
                [('id', 'in', self.recordlist.ids), ('id', '!=', 1)], limit=5)

    def test_search_records(self):
        # TODO: test for context
        with mock.patch.object(self.object, 'search_records') as fake_method:
            self.recordlist.search_records([('id', '!=', 1)], limit=4)
            fake_method.assert_called_with(
                [('id', 'in', self.recordlist.ids), ('id', '!=', 1)], limit=4)

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
        self.assertIsInstance(res, collections.defaultdict)

    def test_existing(self):
        # all existing object ids
        all_obj_ids = self.object.search([], limit=False)

        # generate 10 unexisting ids
        unexistent_ids = list(range(max(all_obj_ids) + 1,
                                    max(all_obj_ids) + 40,
                                    4))
        self.assertEqual(len(unexistent_ids), 10)

        # test simple existense
        rlist = get_record_list(self.object, all_obj_ids[:10] + unexistent_ids)
        self.assertEqual(len(rlist), 20)
        elist = rlist.existing()
        self.assertEqual(len(elist), 10)
        self.assertItemsEqual(elist.ids, all_obj_ids[:10])

        # test existense with repeated items
        rlist_ids = all_obj_ids[:10] + unexistent_ids + all_obj_ids[:5]
        rlist = get_record_list(self.object, rlist_ids)
        self.assertEqual(len(rlist), 25)

        # with uniqify=True (defualt)
        elist = rlist.existing()
        self.assertEqual(len(elist), 10)
        self.assertItemsEqual(elist.ids, all_obj_ids[:10])

        # with uniqify=False
        elist = rlist.existing(uniqify=False)
        self.assertEqual(len(elist), 15)
        self.assertItemsEqual(elist.ids, all_obj_ids[:10] + all_obj_ids[:5])

    def test_refresh(self):
        # save cache pointers to local namespase to simplify access to it
        cache = self.recordlist._cache
        pcache = cache['res.partner']  # partner cache
        ccache = cache['res.country']  # country cache

        # load data to record list
        self.recordlist.prefetch('name', 'country_id.name', 'country_id.code')

        # create related records. This is still required, becuase prefetch
        # just fills cache without creating record instances
        for rec in self.recordlist:
            rec.country_id

        self.assertEqual(len(pcache), len(self.recordlist))
        self.assertGreaterEqual(
            len(ccache),
            1)  # there are atleast on country in cache

        clen = len(ccache)

        for data in pcache.values():
            self.assertItemsEqual(list(data), ['id', 'name', 'country_id'])

        for data in ccache.values():
            if '__name_get_result' in data:
                self.assertItemsEqual(
                    list(data), [
                        'id', 'name', 'code', '__name_get_result'])
            else:
                self.assertItemsEqual(list(data), ['id', 'name', 'code'])

        # refresh recordlist
        self.recordlist.refresh()

        self.assertEqual(len(pcache), len(self.recordlist))
        self.assertEqual(len(ccache), clen)

        # test that data for each partner is empty
        for data in pcache.values():
            self.assertItemsEqual(list(data), ['id'])

        # test that data for each country is empty
        for data in ccache.values():
            self.assertItemsEqual(list(data), ['id'])


class Test_23_Cache(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.cache = empty_cache(self.client)

    def test_client(self):
        self.assertIs(self.cache.client, self.client)

    def test_missing(self):
        obj_cache = self.cache['res.partner']
        self.assertIsInstance(obj_cache, ObjectCache)

        # Test that KeyError is raised on attempt to get cache for object that
        # does not exist in client database
        with self.assertRaises(KeyError):
            self.cache['unexisting.object']

    def test_missing_local(self):
        obj_cache = self.cache['res.partner']

        self.assertFalse(bool(obj_cache))
        self.assertNotIn(42, obj_cache)
        res = obj_cache[42]
        self.assertIsInstance(res, dict)
        self.assertIn('id', res)
        self.assertEqual(len(res), 1)
        self.assertIs(res['id'], 42)
        self.assertIn(42, obj_cache)

    def test_update_keys(self):
        obj_cache = self.cache['res.partner']

        self.assertFalse(bool(obj_cache))
        self.assertNotIn(1, obj_cache)
        self.assertNotIn(2, obj_cache)
        self.assertNotIn(3, obj_cache)
        self.assertNotIn(4, obj_cache)

        # update cache with keys
        obj_cache.update_keys([1, 2, 3])

        self.assertIn(1, obj_cache)
        self.assertEqual(len(obj_cache[1]), 1)
        self.assertIn('id', obj_cache[1])
        self.assertIs(obj_cache[1]['id'], 1)

        self.assertIn(2, obj_cache)
        self.assertEqual(len(obj_cache[2]), 1)
        self.assertIn('id', obj_cache[2])
        self.assertIs(obj_cache[2]['id'], 2)

        self.assertIn(3, obj_cache)
        self.assertEqual(len(obj_cache[3]), 1)
        self.assertIn('id', obj_cache[3])
        self.assertIs(obj_cache[3]['id'], 3)

        self.assertNotIn(4, obj_cache)

        # add new cache keys
        obj_cache.update_keys([3, 4, 6])

        self.assertIn(3, obj_cache)
        self.assertEqual(len(obj_cache[3]), 1)
        self.assertIn('id', obj_cache[3])
        self.assertIs(obj_cache[3]['id'], 3)

        self.assertIn(4, obj_cache)
        self.assertEqual(len(obj_cache[4]), 1)
        self.assertIn('id', obj_cache[4])
        self.assertIs(obj_cache[4]['id'], 4)

        self.assertNotIn(5, obj_cache)

        self.assertIn(6, obj_cache)
        self.assertEqual(len(obj_cache[6]), 1)
        self.assertIn('id', obj_cache[6])
        self.assertIs(obj_cache[6]['id'], 6)

    def test_get_ids_to_read(self):
        obj_cache = self.cache['res.partner']

        # update cache with keys
        obj_cache.update_keys([1, 2, 3, 4, 5])

        self.assertItemsEqual(obj_cache.get_ids_to_read('name'),
                              [1, 2, 3, 4, 5])

        # fill field 'name' in first two cache items
        obj_cache[1]['name'] = 'item 1'
        obj_cache[2]['name'] = 'item 2'

        # See that first two item are not mentioned in result, because they
        # already have value for field 'name'
        self.assertItemsEqual(obj_cache.get_ids_to_read('name'), [3, 4, 5])

        # See that if we get ids to read for fields 'name' and 'address', than
        # all ids will be returned again. this is because no cache item have
        # field 'aaddress' filled
        self.assertItemsEqual(obj_cache.get_ids_to_read('name', 'address'),
                              [1, 2, 3, 4, 5])

        # test that if we change order of fields, nothing will change
        self.assertItemsEqual(obj_cache.get_ids_to_read('address', 'name'),
                              [1, 2, 3, 4, 5])

        # Add value for field 'address' to cache items #3 and #2
        obj_cache[3]['address'] = 'Kyiv, Ukraine'
        obj_cache[2]['address'] = 'Zhytomyr, Ukraine'

        # ad test what ids will be returned
        self.assertItemsEqual(obj_cache.get_ids_to_read('address'), [1, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('name'), [3, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('address', 'name'),
                              [1, 3, 4, 5])

        # Ok, let's add field 'city' to last cache item (#5)
        obj_cache[5]['city'] = 'Kyiv'

        # And look what wi have
        self.assertItemsEqual(obj_cache.get_ids_to_read('address'), [1, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('name'), [3, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('city'), [1, 2, 3, 4])
        self.assertItemsEqual(obj_cache.get_ids_to_read('address', 'name'),
                              [1, 3, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('address', 'city'),
                              [1, 2, 3, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('name', 'city'),
                              [1, 2, 3, 4, 5])
        self.assertItemsEqual(obj_cache.get_ids_to_read('name',
                                                        'address',
                                                        'city'),
                              [1, 2, 3, 4, 5])

    def test_cache_field_str(self):
        obj_cache = self.cache['res.partner']

        # cache is empty
        self.assertFalse(bool(obj_cache))

        obj_cache.cache_field(5, 'char', 'name', 'Test Name')

        self.assertIn(5, obj_cache)
        self.assertIn('id', obj_cache[5])
        self.assertIs(obj_cache[5]['id'], 5)
        self.assertIn('name', obj_cache[5])
        self.assertEqual(obj_cache[5]['name'], 'Test Name')

    def test_cache_field_m2o_int(self):
        obj_cache = self.cache['res.partner']

        # cache is empty
        self.assertFalse(bool(obj_cache))

        obj_cache.cache_field(5, 'many2one', 'user_id', 7)

        # Test that all required data is present in obj_cache
        self.assertIn(5, obj_cache)
        self.assertIn('id', obj_cache[5])
        self.assertIs(obj_cache[5]['id'], 5)
        self.assertIn('user_id', obj_cache[5])
        self.assertEqual(obj_cache[5]['user_id'], 7)

        # Test that related cache filled
        self.assertIn('res.users', self.cache)
        rel_cache = self.cache['res.users']
        self.assertIsInstance(rel_cache, ObjectCache)
        self.assertIn(7, rel_cache)
        self.assertIn('id', rel_cache[7])
        self.assertIs(rel_cache[7]['id'], 7)

    def test_cache_field_m2o_tuple(self):
        obj_cache = self.cache['res.partner']

        # cache is empty
        self.assertFalse(bool(obj_cache))

        obj_cache.cache_field(5, 'many2one', 'user_id', (7, 'Super Admin'))

        # Test that all required data is present in obj_cache
        self.assertIn(5, obj_cache)
        self.assertIn('id', obj_cache[5])
        self.assertIs(obj_cache[5]['id'], 5)
        self.assertIn('user_id', obj_cache[5])

        # value is stored in cache as returned by server, without changed
        self.assertEqual(obj_cache[5]['user_id'], (7, 'Super Admin'))

        # Test that related cache filled
        self.assertIn('res.users', self.cache)
        rel_cache = self.cache['res.users']
        self.assertIsInstance(rel_cache, ObjectCache)
        self.assertIn(7, rel_cache)
        self.assertIn('id', rel_cache[7])
        self.assertIs(rel_cache[7]['id'], 7)

        # Test that name is saved as '__name_get_result' in related cache
        self.assertIn('__name_get_result', rel_cache[7])
        self.assertEqual(rel_cache[7]['__name_get_result'], 'Super Admin')

        # TODO: add tests for many2many and one2many field types
