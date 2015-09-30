from . import BaseTestCase
from openerp_proxy.core import Client


import os
import os.path
import unittest
import time


@unittest.skipUnless(os.environ.get('TEST_DB_SERVICE', False), 'requires DB service test enabled')
class Test_999_DB(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host, protocol=self.env.protocol, port=self.env.port)

    def test_00_dump_drop_restore(self):
        fpath = 'tmp-db-dump.backup'

        # create database if it was not created yet
        if self.env.dbname not in self.client.services.db.list_db():
            self.client.services.db.create_db(self.env.super_password, self.env.dbname, demo=True, admin_password=self.env.password)

        # dump db
        dump_data = self.client.services.db.dump_db(self.env.super_password, self.env.dbname, fpath=fpath)
        self.assertTrue(os.path.exists(fpath))

        # test that rturned data and data written to file are the same
        with open(fpath, 'rb') as f:
            self.assertEqual(f.read(), dump_data)

        # drop it
        self.client.services.db.drop_db(self.env.super_password, self.env.dbname)
        self.assertNotIn(self.env.dbname, self.client.services.db)

        # and try to restore it
        #time.sleep(1)
        self.client.services.db.restore_db(self.env.super_password, self.env.dbname, fpath)
        self.assertIn(self.env.dbname, self.client.services.db)

        # check if objects were restored
        time.sleep(2)
        cl = self.client.login(self.env.dbname, self.env.user, self.env.password)
        self.assertIsNotNone(cl.uid)
        self.assertIsNotNone(cl.user)

        os.unlink(fpath)
