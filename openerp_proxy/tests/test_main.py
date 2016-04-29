from . import BaseTestCase
from .. import Session

import os
import os.path

from ..main import (generate_header_aliases,
                    generate_header_databases)


class Test_95_Main(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self._session_file_path = '/tmp/openerp_proxy.main.test.json'

    def tearDown(self):
        if os.path.exists(self._session_file_path):
            os.unlink(self._session_file_path)

    def test_01_empty_session(self):
        session = Session(self._session_file_path)
        expected_header_aliases = "\n"
        expected_header_databases = "\n"
        self.assertEqual(expected_header_aliases,
                         generate_header_aliases(session))
        self.assertEqual(expected_header_databases,
                         generate_header_databases(session))

    def test_10_one_db_no_aliases(self):
        session = Session(self._session_file_path)
        cl = session.connect(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port,
                             interactive=False)

        expected_header_aliases = "\n"
        expected_header_databases = "\n        - [  1] %s\n" % cl.get_url()
        self.assertEqual(expected_header_aliases,
                         generate_header_aliases(session))
        self.assertEqual(expected_header_databases,
                         generate_header_databases(session))

    def test_20_one_db_one_aliase(self):
        session = Session(self._session_file_path)
        cl = session.connect(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port,
                             interactive=False)

        aliase = 'my_aliase'
        session.aliase(aliase, cl)

        expected_header_aliases = "\n        - %s: %s\n" % (aliase,
                                                            cl.get_url())
        expected_header_databases = "\n        - [  1] %s\n" % cl.get_url()

        self.assertEqual(expected_header_aliases,
                         generate_header_aliases(session))
        self.assertEqual(expected_header_databases,
                         generate_header_databases(session))
