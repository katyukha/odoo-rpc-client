import unittest
import pkg_resources

from . import BaseTestCase
from ..client import Client
from ..orm.object import Object
from ..orm.record import Record
from ..service.service import ServiceManager
from ..plugin import Plugin

VERSION_CLASSES = (pkg_resources.SetuptoolsLegacyVersion,
                   pkg_resources.SetuptoolsVersion)


class Test_10_Client(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_120_username(self):
        self.assertEqual(self.client.username, self.env.user)
        self.assertIsInstance(self.client.user, Record)
        self.assertEqual(self.client.user.login, self.env.user)

    def test_122_user_context(self):
        uctx = self.client.user_context
        self.assertDictEqual(
            uctx,
            self.client.get_obj('res.users').context_get())

    def test_125_server_version(self):
        # Check that server version is wrapped in parse_version. thus allows to
        # compare versions
        self.assertIsInstance(self.client.server_version, VERSION_CLASSES)

    def test_126_database_version_full(self):
        # Check that database full version is wrapped in parse_version.
        # thus allows to compare versions
        self.assertIsInstance(self.client.database_version_full,
                              VERSION_CLASSES)

    def test_127_database_version(self):
        # Check that database version is wrapped in parse_version.
        # thus allows to compare versions
        self.assertIsInstance(
            self.client.database_version, VERSION_CLASSES)

    def test_128_database_version_eq_server_version(self):
        self.assertEqual(self.client.server_version,
                         self.client.database_version)

    def test_130_get_obj(self):
        self.assertIn('res.partner', self.client.registered_objects)
        obj = self.client.get_obj('res.partner')
        self.assertIsInstance(obj, Object)

        # Check object access in dictionary style
        self.assertIs(obj, self.client['res.partner'])

    def test_142_get_obj_wrong(self):
        self.assertNotIn(
            'bad.object.name',
            self.client.registered_objects)
        with self.assertRaises(ValueError):
            self.client.get_obj('bad.object.name')

        with self.assertRaises(KeyError):
            self.client['bad.object.name']

    def test_150_to_url(self):
        url_tmpl = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s"
        cl_url = url_tmpl % self.env
        self.assertEqual(Client.to_url(self.client), cl_url)
        self.assertEqual(Client.to_url(self.env), cl_url)
        self.assertEqual(Client.to_url(None, **self.env), cl_url)
        self.assertEqual(self.client.get_url(), cl_url)

        with self.assertRaises(ValueError):
            Client.to_url('strange thing')

    def test_155_str(self):
        self.assertEqual(str(self.client), u"Client: %s" %
                         self.client.get_url())

    def test_155_repr(self):
        self.assertEqual(repr(self.client), str(self.client))

    def test_160_plugins(self):
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
            "odoo_rpc_client.plugin.PluginManager [%d]" % len(
                self.client.plugins))
        self.assertEqual(
            repr(self.client.plugins),
            "<odoo_rpc_client.plugin.PluginManager [%d]>" % len(
                self.client.plugins))
        self.assertEqual(
            str(self.client.plugins.Test),
            "odoo_rpc_client.plugin.Plugin:Test")
        self.assertEqual(
            repr(self.client.plugins.Test),
            "<odoo_rpc_client.plugin.Plugin:Test>")

    def test_162_plugins_wrong_name(self):
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

    def test_170_client_services(self):
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
        self.assertEqual(
            str(self.client.services.report), u"Service 'report' of %s" %
            self.client)
        self.assertEqual(
            repr(self.client.services.report), u"<Service 'report' of %s>" %
            self.client)

        with self.assertRaises(AttributeError):
            self.client.services._private_service

    def test_180_execute_lt_v10(self):
        if self.client.server_version >= pkg_resources.parse_version('10.0'):
            raise unittest.SkipTest('Not applicable to Odoo 10.0')

        res = self.client.execute('res.partner', 'read', 1)
        self.assertIsInstance(res, dict)
        self.assertEqual(res['id'], 1)

        res = self.client.execute('res.partner', 'read', [1])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], dict)
        self.assertEqual(res[0]['id'], 1)

    def test_181_execute_gte_v10(self):
        if self.client.server_version < pkg_resources.parse_version('10.0'):
            raise unittest.SkipTest(
                'Not applicable to Odoo version less then 10.0')

        res = self.client.execute('res.partner', 'read', 1)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], dict)
        self.assertEqual(res[0]['id'], 1)

        res = self.client.execute('res.partner', 'read', [1])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], dict)
        self.assertEqual(res[0]['id'], 1)

    def test_190_not_equal(self):
        self.assertNotEqual(self.client, 42)

    def test_200_clean_caches(self):
        self.assertIsNotNone(self.client.user_context)
        self.assertIn('lang', self.client.user_context)

        self.client.clean_caches()

        self.assertIsNone(self.client._user)
        self.assertIsNotNone(self.client._username)
        self.assertIsNone(self.client._user_context)

    def test_210_from_url_host_port(self):
        cl = Client.from_url("%(host)s:%(port)s/" % self.env)
        self.assertIsInstance(cl, Client)
        self.assertEqual(cl.get_url(),
                         "xml-rpc://None@%(host)s:%(port)s/None" % self.env)

    def test_211_from_url_protocol_host_port_user_db(self):
        cl = Client.from_url(
            "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s" % self.env)
        self.assertIsInstance(cl, Client)

    def test_212_from_url_protocol_host_port_user_db(self):
        cl = Client.from_url(
            "%(protocol)s://%(user)s:%(password)s@%(host)s:%(port)s/"
            "%(dbname)s" % self.env)
        self.assertIsInstance(cl, Client)
        self.assertEqual(cl.user.login, self.env['user'])

    def test_220_ref_existing(self):
        partner = self.client.ref('base.main_partner')
        self.assertIsInstance(partner, Record)
        self.assertEqual(partner._object.name, 'res.partner')

    def test_221_ref_un_existing(self):
        partner = self.client.ref('base.unexisting_partner_id')
        self.assertIsInstance(partner, bool)
        self.assertFalse(partner)

    def test_222_ref_no_module_spec(self):
        with self.assertRaises(ValueError):
            self.client.ref('main_partner')  # no module specified
