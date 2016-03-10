from pkg_resources import parse_version

from . import BaseTestCase
from ..core import Client
from ..orm.object import Object
from ..orm.record import Record
from ..service.service import ServiceManager
from ..plugin import Plugin


class Test_10_Client(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_20_username(self):
        self.assertEqual(self.client.username, self.env.user)
        self.assertIsInstance(self.client.user, Record)
        self.assertEqual(self.client.user.login, self.env.user)

    def test_22_user_context(self):
        uctx = self.client.user_context
        self.assertDictEqual(
            uctx,
            self.client.get_obj('res.users').context_get())

    def test_25_server_version(self):
        # Check that server version is wrapped in parse_version. thus allows to
        # compare versions
        self.assertIsInstance(
            self.client.server_version, type(
                parse_version('1.0.0')))

    def test_30_get_obj(self):
        self.assertIn('res.partner', self.client.registered_objects)
        obj = self.client.get_obj('res.partner')
        self.assertIsInstance(obj, Object)

        # Check object access in dictionary style
        self.assertIs(obj, self.client['res.partner'])

    def test_42_get_obj_wrong(self):
        self.assertNotIn(
            'bad.object.name',
            self.client.registered_objects)
        with self.assertRaises(ValueError):
            self.client.get_obj('bad.object.name')

        with self.assertRaises(KeyError):
            self.client['bad.object.name']

    def test_50_to_url(self):
        url_tmpl = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s"
        cl_url = url_tmpl % self.env
        self.assertEqual(Client.to_url(self.client), cl_url)
        self.assertEqual(Client.to_url(self.env), cl_url)
        self.assertEqual(Client.to_url(None, **self.env), cl_url)
        self.assertEqual(self.client.get_url(), cl_url)

        with self.assertRaises(ValueError):
            Client.to_url('strange thing')

    def test_55_str(self):
        self.assertEqual(str(self.client), u"Client: %s" %
                         self.client.get_url())

    def test_55_repr(self):
        self.assertEqual(repr(self.client), str(self.client))

    def test_60_plugins(self):
        self.assertIn('Test', self.client.plugins.registered_plugins)
        self.assertIn('Test', self.client.plugins)
        self.assertIn(
            'Test', dir(
                self.client.plugins))  # for introspection
        # iteration over plugins names
        self.assertIn('Test', [p for p in self.client.plugins])
        self.assertIsInstance(self.client.plugins.Test, Plugin)
        self.assertIsInstance(self.client.plugins['Test'], Plugin)
        self.assertIs(
            self.client.plugins['Test'],
            self.client.plugins.Test)

        # check plugin's method result
        self.assertEqual(
            self.client.plugins.Test.test(),
            self.client.get_url())

        # Check plugin representation
        self.assertEqual(
            str(self.client.plugins),
            "openerp_proxy.plugin.PluginManager [%d]" % len(
                self.client.plugins))
        self.assertEqual(
            repr(self.client.plugins),
            "<openerp_proxy.plugin.PluginManager [%d]>" % len(
                self.client.plugins))
        self.assertEqual(
            str(self.client.plugins.Test),
            "openerp_proxy.plugin.Plugin:Test")
        self.assertEqual(
            repr(self.client.plugins.Test),
            "<openerp_proxy.plugin.Plugin:Test>")

    def test_62_plugins_wrong_name(self):
        self.assertNotIn(
            'Test_Bad',
            self.client.plugins.registered_plugins)
        self.assertNotIn('Test_Bad', self.client.plugins)
        self.assertNotIn(
            'Test_Bad', dir(
                self.client.plugins))  # for introspection

        with self.assertRaises(KeyError):
            self.client.plugins['Test_Bad']

        with self.assertRaises(AttributeError):
            self.client.plugins.Test_Bad

    def test_70_client_services(self):
        self.assertIsInstance(self.client.services, ServiceManager)
        self.assertIn('db', self.client.services)
        self.assertIn('object', self.client.services)
        self.assertIn('report', self.client.services)

        self.assertIn('db', self.client.services.service_list)
        self.assertIn('object', self.client.services.service_list)
        self.assertIn('report', self.client.services.service_list)

        self.assertIn('db', dir(self.client.services))
        self.assertIn('object', dir(self.client.services))
        self.assertIn('report', dir(self.client.services))

        # Test representations:
        self.assertEqual(
            str(self.client.services), u"ServiceManager for %s" %
            self.client)
        self.assertEqual(
            repr(self.client.services), u"<ServiceManager for %s>" %
            self.client)
        self.assertEqual(
            str(self.client.services.db), u"Service 'db' of %s" %
            self.client)
        self.assertEqual(
            repr(self.client.services.db), u"<Service 'db' of %s>" %
            self.client)

        with self.assertRaises(AttributeError):
            self.client.services._private_service

    def test_80_execute(self):
        res = self.client.execute('res.partner', 'read', 1)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['id'], 1)

        res = self.client.execute('res.partner', 'read', [1])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], dict)
        self.assertEqual(res[0]['id'], 1)

    def test_90_not_equal(self):
        self.assertNotEqual(self.client, 42)

    def test_100_clean_caches(self):
        self.assertIsNotNone(self.client.user_context)
        self.assertIn('lang', self.client.user_context)

        self.client.clean_caches()

        self.assertIsNone(self.client._user)
        self.assertIsNotNone(self.client._username)
        self.assertIsNone(self.client._user_context)
