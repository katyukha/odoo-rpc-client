from . import BaseTestCase
from ..core import Client
from ..exceptions import LoginException
from ..connection import get_connector_names


class Test_00_Connection(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_00_connection_simple(self):
        client = self.client
        self.assertIsNone(client.username)
        self.assertIsNone(client.dbname)

        # access to uid with out credentials provided, should cause error
        with self.assertRaises(LoginException):
            client.uid

        # access to uid with out credentials provided, should cause error
        with self.assertRaises(LoginException):
            client.user

    def test_01_create_db(self):
        client = self.client
        if self.env.dbname in client.services.db.list_db():
            self.assertIn(self.env.dbname, client.services.db)

            if self.recreate_db:
                client.services.db.drop_db(self.env.super_password,
                                           self.env.dbname)
            else:
                return self.skipTest("Database already created")

        self.assertNotIn(self.env.dbname, client.services.db)

        cl = client.services.db.create_db(self.env.super_password,
                                          self.env.dbname,
                                          demo=True,
                                          admin_password=self.env.password)

        self.assertIn(self.env.dbname, client.services.db)
        # cl is object of same class as client, but with credential filled
        self.assertIsInstance(cl, Client)

        # test that uid and user properties are accessible
        self.assertIsNotNone(cl.uid)
        self.assertIsNotNone(cl.user)

    def test_02_connect(self):
        client = self.client
        cl = client.connect(dbname=self.env.dbname,
                            user=self.env.user,
                            pwd=self.env.password)

        # cl is object of same class as client, but with credential filled
        self.assertIsInstance(cl, Client)

        # test that uid and user properties are accessible
        self.assertIsNotNone(cl.uid)
        self.assertIsNotNone(cl.user)

    def test_03_login(self):
        client = self.client
        cl = client.login(self.env.dbname, self.env.user, self.env.password)

        # cl is object of same class as client, but with credential filled
        self.assertIsInstance(cl, Client)

        # test that uid and user properties are accessible
        self.assertIsNotNone(cl.uid)
        self.assertIsNotNone(cl.user)

    def test_04_login_wrong(self):
        client = self.client

        with self.assertRaises(LoginException):
            wrong_password = self.env.password + "-wrong"
            cl = client.login(self.env.dbname, self.env.user, wrong_password)
            # Note, that login return's new instance of client,
            # and we need to acces uid property,
            # to make it try to login via RPC.
            cl.uid

    def test_05_reconnect(self):
        client = self.client
        cl = client.login(self.env.dbname, self.env.user, self.env.password)
        old_uid = cl.uid

        new_uid = cl.reconnect()
        self.assertEqual(old_uid, new_uid)
        self.assertEqual(old_uid, cl.uid)

    def test_06_get_connector_names(self):
        self.assertItemsEqual(get_connector_names(),
                              ['json-rpc', 'json-rpcs', 'xml-rpc', 'xml-rpcs'])
