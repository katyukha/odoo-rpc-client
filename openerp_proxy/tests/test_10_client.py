from . import BaseTestCase
from openerp_proxy.core import Client
from openerp_proxy.orm.object import Object
from openerp_proxy.orm.record import Record
from openerp_proxy.plugin import Plugin
from openerp_proxy.exceptions import LoginException


class TestClient(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_00_username(self):
        self.assertEqual(self.client.username, self.env.user)
        self.assertIsInstance(self.client.user, Record)
        self.assertEqual(self.client.user.login, self.env.user)

    def test_10_get_obj(self):
        self.assertIn('res.partner', self.client.registered_objects)
        obj = self.client.get_obj('res.partner')
        self.assertIsInstance(obj, Object)

        # Check object access in dictionary style
        self.assertIs(obj, self.client['res.partner'])

    def test_12_get_obj_wrong(self):
        self.assertNotIn('bad.object.name', self.client.registered_objects)
        with self.assertRaises(ValueError):
            self.client.get_obj('bad.object.name')

        with self.assertRaises(KeyError):
            self.client['bad.object.name']

    def test_20_to_url(self):
        url_tmpl = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s"
        cl_url = url_tmpl % self.env
        self.assertEqual(Client.to_url(self.client), cl_url)
        self.assertEqual(Client.to_url(self.env), cl_url)
        self.assertEqual(Client.to_url(None, **self.env), cl_url)
        self.assertEqual(self.client.get_url(), cl_url)

    def test_30_plugins(self):
        self.assertIn('Test', self.client.plugins.registered_plugins)
        self.assertIn('Test', self.client.plugins)
        self.assertIn('Test', dir(self.client.plugins))  # for introspection
        self.assertIsInstance(self.client.plugins.Test, Plugin)
        self.assertIsInstance(self.client.plugins['Test'], Plugin)
        self.assertIs(self.client.plugins['Test'], self.client.plugins.Test)

        # check plugin's method result
        self.assertEqual(self.client.get_url(), self.client.plugins.Test.test())

    def test_32_plugins_wrong_name(self):
        self.assertNotIn('Test_Bad', self.client.plugins.registered_plugins)
        self.assertNotIn('Test_Bad', self.client.plugins)
        self.assertNotIn('Test_Bad', dir(self.client.plugins))  # for introspection

        with self.assertRaises(KeyError):
            self.client.plugins['Test_Bad']

        with self.assertRaises(AttributeError):
            self.client.plugins.Test_Bad
