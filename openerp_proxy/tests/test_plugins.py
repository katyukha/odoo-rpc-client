from . import BaseTestCase
from .. import Client
from ..orm import Record

import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock


class Test_25_Plugin_ModuleUtils(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)

    def test_10_init_module_utils(self):
        self.assertNotIn('module_utils', self.client.plugins)
        self.assertEqual(len(self.client.plugins), 1)
        self.assertIn('Test', self.client.plugins)

        import openerp_proxy.plugins.module_utils

        self.assertIn('module_utils', self.client.plugins)
        self.assertEqual(len(self.client.plugins), 2)

    def test_15_modules(self):
        self.assertIn('sale', self.client.plugins.module_utils.modules)

    def test_20_modules_dir(self):
        self.assertIn('m_sale', dir(self.client.plugins.module_utils))

    def test_25_module_getitem(self):
        res = self.client.plugins.module_utils['sale']
        self.assertIsInstance(res, Record)
        self.assertEqual(res._object.name, 'ir.module.module')

        from openerp_proxy.plugins.module_utils import ModuleObject

        self.assertIn(ModuleObject, res._object.__class__.__bases__)

    def test_30_module_getattr(self):
        res = self.client.plugins.module_utils.m_sale

        self.assertIsInstance(res, Record)
        self.assertEqual(res._object.name, 'ir.module.module')

        from openerp_proxy.plugins.module_utils import ModuleObject

        self.assertIn(ModuleObject, res._object.__class__.__bases__)

        with self.assertRaises(AttributeError):
            self.client.plugins.module_utils.m_unexistent_module

    def test_35_module_install(self):
        smod = self.client.plugins.module_utils.m_sale

        if smod.state == 'installed':
            raise unittest.SkipTest('Module already installed')

        self.assertNotEqual(smod.state, 'installed')
        smod.install()
        smod.refresh()  # reread data from database
        self.assertEqual(smod.state, 'installed')

    def test_40_module_upgrade(self):
        smod = self.client.plugins.module_utils.m_sale

        self.assertEqual(smod.state, 'installed')
        smod.upgrade()  # just call it
