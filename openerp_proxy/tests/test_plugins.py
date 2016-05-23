from . import BaseTestCase
from .. import Client
from ..orm import (Record,
                   RecordList)

import unittest


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

        import openerp_proxy.plugins.module_utils  # noqa

        self.assertIn('module_utils', self.client.plugins)
        self.assertEqual(len(self.client.plugins), 2)

    def test_15_modules(self):
        self.assertIsInstance(self.client.plugins.module_utils.modules, dict)
        self.assertIn('sale', self.client.plugins.module_utils.modules)
        self.assertIsInstance(self.client.plugins.module_utils.modules['sale'],
                              Record)
        self.assertEqual(
            self.client.plugins.module_utils.modules['sale']._object.name,
            'ir.module.module')

    def test_20_modules_dir(self):
        self.assertIn('m_sale', dir(self.client.plugins.module_utils))
        self.assertIn('modules', dir(self.client.plugins.module_utils))
        self.assertIn('update_module_list',
                      dir(self.client.plugins.module_utils))
        self.assertIn('installed_modules',
                      dir(self.client.plugins.module_utils))

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

    def test_35_module_contains(self):
        self.assertIsNone(self.client.plugins.module_utils._modules)
        self.assertIn('sale', self.client.plugins.module_utils)
        self.assertNotIn(
            'some strange unexistent module',
            self.client.plugins.module_utils)
        self.assertIsNotNone(self.client.plugins.module_utils._modules)

    def test_40_module_install(self):
        smod = self.client.plugins.module_utils.m_sale

        if smod.state == 'installed':
            raise unittest.SkipTest('Module already installed')

        self.assertNotEqual(smod.state, 'installed')
        smod.install()
        smod.refresh()  # reread data from database
        self.assertEqual(smod.state, 'installed')

    def test_45_update_module_list(self):
        # touch modules proerty to load module info
        self.client.plugins.module_utils.modules

        self.assertIsNotNone(self.client.plugins.module_utils._modules)
        self.client.plugins.module_utils.update_module_list()
        self.assertIsNone(self.client.plugins.module_utils._modules)

    def test_50_module_upgrade(self):
        smod = self.client.plugins.module_utils.m_sale

        self.assertEqual(smod.state, 'installed')
        smod.upgrade()  # just call it

    def test_55_installed_modules(self):
        modules = self.client.plugins.module_utils.installed_modules
        modules2 = self.client['ir.module.module'].search_records(
            [('state', '=', 'installed')])
        self.assertItemsEqual(modules, modules2)


class Test_26_Plugin_ExternalIDS(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.client = Client(self.env.host,
                             dbname=self.env.dbname,
                             user=self.env.user,
                             pwd=self.env.password,
                             protocol=self.env.protocol,
                             port=self.env.port)
        self.data_obj = self.client['ir.model.data']
        self.partner_obj = self.client['res.partner']
        main_partner_domain = [
            ('module', '=', 'base'),
            ('model', '=', 'res.partner'),
            ('name', '=', 'main_partner'),
        ]
        self.main_partner_data = self.data_obj.search_records(
            main_partner_domain)[0]
        self.main_partner = self.partner_obj.browse(
            self.main_partner_data.res_id)

    def test_10_init_module_utils(self):
        self.assertNotIn('external_ids', self.client.plugins)
        self.assertIn('Test', self.client.plugins)

        import openerp_proxy.plugins.external_ids  # noqa

        self.assertIn('external_ids', self.client.plugins)

    def test_20_get_for__record(self):
        data = self.client.plugins.external_ids.get_for(self.main_partner)
        self.assertIsInstance(data, RecordList)
        self.assertEqual(data.object.name, 'ir.model.data')
        self.assertEqual(len(data), 1)

        data0 = data[0]
        self.assertEqual(data0.model, 'res.partner')
        self.assertEqual(data0.res_id, self.main_partner.id)
        self.assertEqual(data0.module, 'base')

    def test_21_get_for__recordlist(self):
        recordlist = self.client['res.partner'].search_records([], limit=10)
        res = self.client.plugins.external_ids.get_for(recordlist)

        self.assertIsInstance(res, RecordList)
        self.assertEqual(res.object.name, 'ir.model.data')

        for data in res:
            self.assertIn(data.res_id, recordlist.ids)

    def test_22_get_for__tuple(self):
        data = self.client.plugins.external_ids.get_for(('res.partner',
                                                         self.main_partner.id))
        self.assertIsInstance(data, RecordList)
        self.assertEqual(data.object.name, 'ir.model.data')
        self.assertEqual(len(data), 1)

        data0 = data[0]
        self.assertEqual(data0.model, 'res.partner')
        self.assertEqual(data0.res_id, self.main_partner.id)
        self.assertEqual(data0.module, 'base')

    def test_23_get_for__str(self):
        data = self.client.plugins.external_ids.get_for('base.main_partner')
        self.assertIsInstance(data, RecordList)
        self.assertEqual(data.object.name, 'ir.model.data')
        self.assertEqual(len(data), 1)

        data0 = data[0]
        self.assertEqual(data0.model, 'res.partner')
        self.assertEqual(data0.res_id, self.main_partner.id)
        self.assertEqual(data0.module, 'base')

    def test_23_get_for__str_module(self):
        data = self.client.plugins.external_ids.get_for('main_partner', 'base')
        self.assertIsInstance(data, RecordList)
        self.assertEqual(data.object.name, 'ir.model.data')
        self.assertEqual(len(data), 1)

        data0 = data[0]
        self.assertEqual(data0.model, 'res.partner')
        self.assertEqual(data0.res_id, self.main_partner.id)
        self.assertEqual(data0.module, 'base')

    def test_24_get_for__bad_value(self):
        with self.assertRaises(ValueError):
            self.client.plugins.external_ids.get_for(None, 'base')

    def test_25_get_for__unexisting_xml_id(self):
        data = self.client.plugins.external_ids.get_for(
            'base.unexisting_xml_id')
        self.assertIsInstance(data, RecordList)
        self.assertEqual(data.length, 0)
        self.assertFalse(data)

    def test_26_get_for__wrong_xml_id(self):
        with self.assertRaises(ValueError):
            self.client.plugins.external_ids.get_for('bad_xml_id')

    def test_30_get_xmlid(self):
        xml_id = self.client.plugins.external_ids.get_xmlid(self.main_partner)
        self.assertEqual(xml_id, "base.main_partner")

        # Create new partner without xml_id
        new_partner_id = self.client[
            'res.partner'].create({'name': 'Test partner'})
        new_partner = self.client['res.partner'].browse(new_partner_id)

        no_xml_id = self.client.plugins.external_ids.get_xmlid(new_partner)
        self.assertFalse(no_xml_id)

        # Cleanup, remove created partner
        new_partner.unlink()

    def test_35_get_record(self):
        mpartner = self.client.plugins.external_ids.get_record(
            'base.main_partner')
        self.assertEqual(mpartner, self.main_partner)

        no_partner = self.client.plugins.external_ids.get_record(
            'base.unexisting_xml_id')
        self.assertFalse(no_partner)

    def test_40_record_as_xmlid(self):
        xml_id = self.main_partner.as_xmlid()
        self.assertEqual(xml_id, "base.main_partner")

        new_partner_id = self.client[
            'res.partner'].create({'name': 'Test partner'})
        new_partner = self.client['res.partner'].browse(new_partner_id)

        no_xml_id = new_partner.as_xmlid()
        self.assertFalse(no_xml_id)

        # Cleanup, remove created partner
        new_partner.unlink()
