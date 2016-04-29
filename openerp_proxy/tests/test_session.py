from . import BaseTestCase
from .. import (Client,
                Session)
import sys
import os
import os.path


class Test_90_Session(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self._session_file_path = '/tmp/openerp_proxy.session.json'

    def tearDown(self):
        if os.path.exists(self._session_file_path):
            os.unlink(self._session_file_path)

    def test_01_init_save(self):
        session = Session(self._session_file_path)
        self.assertFalse(os.path.exists(self._session_file_path))
        session.save()
        self.assertTrue(os.path.exists(self._session_file_path))

    def test_05_add_path(self):
        old_sys_path = sys.path[:]
        self.assertNotIn('/new_path', sys.path)
        session = Session(self._session_file_path)
        session.add_path('/new_path')
        self.assertIn('/new_path', sys.path)
        session.save()
        del session
        sys.path = old_sys_path[:]
        self.assertNotIn('/new_path', sys.path)

        # test that path is automaticaly added on new session init
        session = Session(self._session_file_path)
        self.assertIn('/new_path', sys.path)
        del session
        sys.path = old_sys_path[:]
        self.assertNotIn('/new_path', sys.path)

    def test_10_option(self):
        session = Session(self._session_file_path)
        self.assertIs(session.option('store_passwords'), None)
        session.option('store_passwords', True)
        self.assertTrue(session.option('store_passwords'))
        session.save()
        del session

        session = Session(self._session_file_path)
        self.assertTrue(session.option('store_passwords'))

    def test_15_connect_save_connect(self):
        session = Session(self._session_file_path)

        # set store_passwords to true, to avoid password promt during tests
        session.option('store_passwords', True)

        cl = session.connect(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port,
                             interactive=False)

        self.assertIsInstance(cl, Client)
        self.assertIn(cl.get_url(), session._databases)
        self.assertIn(cl.get_url(), session.db_list)
        self.assertEqual(len(session.db_list), 1)
        self.assertIs(session.get_db(cl.get_url()), cl)

        # first db must be with index=1
        self.assertEqual(session.index[1], cl.get_url())

        # index and url may be used in this way too
        self.assertIs(session[cl.get_url()], cl)
        self.assertIs(session[1], cl)

        # test that when connecting again with same args via session, new
        # Client instances will NOT be created
        cl2 = session.connect(self.env.host,
                              dbname=self.env.dbname,
                              user=self.env.user,
                              pwd=self.env.password,
                              protocol=self.env.protocol,
                              port=self.env.port,
                              interactive=False)
        self.assertIs(cl, cl2)

        # save the session
        session.save()
        del session

        # recreate session
        session = Session(self._session_file_path)

        # and test again
        self.assertIn(cl.get_url(), session._databases)
        self.assertIn(cl.get_url(), session.db_list)
        self.assertEqual(len(session.db_list), 1)
        self.assertIsNot(session.get_db(cl.get_url()), cl)
        self.assertEqual(session.get_db(cl.get_url()), cl)

        # first db must be with index=1
        self.assertEqual(session.index[1], cl.get_url())
        self.assertIsNot(session[cl.get_url()], cl)
        self.assertIsNot(session[1], cl)
        self.assertEqual(session[cl.get_url()], cl)
        self.assertEqual(session[1], cl)
        del session

        # test situation when session just started and saved, without changes
        # this code is aimed mostly to increase test coverage. In this case in
        # ._databases all values will be dict when saveing
        session = Session(self._session_file_path)
        session.save()

    def test_20_connect_save_connect_no_save(self):
        session = Session(self._session_file_path)

        # set store_passwords to true, to avoid password promt during tests
        session.option('store_passwords', True)

        cl = session.connect(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port,
                             interactive=False,
                             no_save=True)   # diff from previous test

        self.assertIsInstance(cl, Client)
        self.assertIn(cl.get_url(), session._databases)
        self.assertIn(cl.get_url(), session.db_list)
        self.assertEqual(len(session.db_list), 1)
        self.assertIs(session.get_db(cl.get_url()), cl)

        # first db must be with index=1
        self.assertEqual(session.index[1], cl.get_url())

        # index and url may be used in this way too
        self.assertIs(session[cl.get_url()], cl)
        self.assertIs(session[1], cl)

        # save the session
        session.save()
        del session

        # recreate session
        session = Session(self._session_file_path)

        # and test again
        self.assertNotIn(cl.get_url(), session._databases)
        self.assertNotIn(cl.get_url(), session.db_list)
        self.assertEqual(len(session.db_list), 0)

        with self.assertRaises(ValueError):
            session.get_db(cl.get_url())

        with self.assertRaises(KeyError):
            session[cl.get_url()]

    def test_25_aliases(self):
        session = Session(self._session_file_path)

        # set store_passwords to true, to avoid password promt during tests
        session.option('store_passwords', True)

        cl = session.connect(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port,
                             interactive=False)

        self.assertEqual(len(session.aliases), 0)

        res = session.aliase('cl1', cl)
        self.assertIs(res, cl)

        res = session.aliase('cl2', 1)  # use index
        self.assertIs(res, 1)

        res = session.aliase('cl3', cl.get_url())  # use url
        self.assertEqual(res, cl.get_url())

        with self.assertRaises(ValueError):
            session.aliase('cl4', 'bad url')

        self.assertIn('cl1', session.aliases)
        self.assertIs(session.get_db('cl1'), cl)
        self.assertIs(session['cl1'], cl)
        self.assertIs(session.cl1, cl)

        self.assertIs(session.cl1, session.cl2)
        self.assertIs(session.cl1, session.cl3)
        self.assertIn('cl1', dir(session))

        # Test taht normal attributes in dir
        self.assertIn('aliases', dir(session))

        # save the session
        session.save()
        del session

        # recreate session
        session = Session(self._session_file_path)

        # and test again
        self.assertTrue(bool(session.index))
        self.assertEqual(len(session.aliases), 3)
        self.assertIn('cl1', session.aliases)
        self.assertEqual(session.get_db('cl1'), cl)
        self.assertEqual(session['cl1'], cl)
        self.assertEqual(session.cl1, cl)

        self.assertIs(session.cl1, session.cl2)
        self.assertIs(session.cl1, session.cl3)

        with self.assertRaises(AttributeError):
            session.unexistent_aliase

        self.assertIn('cl1', dir(session))
