from . import BaseTestCase
from ..core import Client


import os
import os.path
import unittest
import time
import six


@unittest.skipUnless(os.environ.get('TEST_DB_SERVICE', False),
                     'requires DB service test enabled')
class Test_999_DB(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_00_create_db(self):
        # create database if it was not created yet
        if self.env.dbname not in self.client.services.db.list_db():
            self.client.services.db.create_db(self.env.super_password,
                                              self.env.dbname, demo=True,
                                              admin_password=self.env.password)
        else:
            raise unittest.SkipTest("database already creaated. "
                                    "no need to create it")

    def test_10_to_dbname(self):
        cl_db = self.client.login(self.env.dbname, 'admin', self.env.password)

        from openerp_proxy.service.db import to_dbname

        res = to_dbname(self.env.dbname)
        self.assertEqual(res, self.env.dbname)
        self.assertIsInstance(res, six.string_types)

        res = to_dbname(cl_db)
        self.assertEqual(res, self.env.dbname)
        self.assertIsInstance(res, six.string_types)

        # Test that value error is raise when unexpected value passed to
        # function
        with self.assertRaises(ValueError):
            to_dbname(25)

    def test_20_dump_drop_restore(self):
        # dump db
        dump_data = self.client.services.db.dump_db(self.env.super_password,
                                                    self.env.dbname)
        self.assertIsInstance(dump_data, bytes)

        # drop it
        self.client.services.db.drop_db(self.env.super_password,
                                        self.env.dbname)
        self.assertNotIn(self.env.dbname, self.client.services.db)

        # and try to restore it
        self.client.services.db.restore_db(self.env.super_password,
                                           self.env.dbname,
                                           dump_data)
        self.assertIn(self.env.dbname, self.client.services.db)

        # check if objects were restored
        time.sleep(2)
        cl = self.client.login(self.env.dbname,
                               self.env.user,
                               self.env.password)
        self.assertIsNotNone(cl.uid)
        self.assertIsNotNone(cl.user)
