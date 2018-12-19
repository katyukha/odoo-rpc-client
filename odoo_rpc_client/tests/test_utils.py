# -*- coding: utf-8 -*-
# Copyright © 2014-2018 Dmytro Katyukha <dmytro.katyukha@gmail.com>

#######################################################################
# This Source Code Form is subject to the terms of the Mozilla Public #
# License, v. 2.0. If a copy of the MPL was not distributed with this #
# file, You can obtain one at http://mozilla.org/MPL/2.0/.            #
#######################################################################

import six

from . import BaseTestCase
from .. import utils


class Test_100_Utils_ustr(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()

        # Note, if cp1251 will be first, than tests will fail
        # because following code will not throw errors:
        #    u'Юнікод'.encode('utf8').decode('cp1251')
        self.ustr2 = utils.UConverter(['utf8', 'cp1251', 'ascii'])

        class UObj(object):
            if six.PY3:
                def __str__(self):
                    return u"Юнікод"
            elif six.PY2:
                def __unicode__(self):
                    return u"Юнікод"

        class BObj(object):
            if six.PY3:
                # TODO: Is this correct for python3
                # for python 3 repr will be called
                def __str__(self):
                    return u"Юнікод"
            elif six.PY2:
                def __str__(self):
                    return u"Юнікод".encode('utf-8')

        self.uobj = UObj()
        self.bobj = BObj()

    def test_ustr_unicode(self):
        ustr = utils.ustr

        self.assertIsInstance(ustr(u"Юнікод"), six.text_type)
        self.assertIs(ustr(u"Юнікод"), u"Юнікод")

    def test_ustr_bytes(self):
        ustr = utils.ustr

        self.assertIsInstance(u"Юнікод".encode("utf-8"), six.binary_type)
        self.assertIsInstance(ustr(u"Юнікод".encode("utf-8")), six.text_type)
        self.assertEqual(ustr(u"Юнікод".encode("utf-8")), u"Юнікод")

    def test_ustr_bytes_cp1251(self):
        ustr = utils.ustr

        # cp1251 encoding is not recognized by ustr (only utf8 and ascii)
        self.assertIsInstance(u"Юнікод".encode("cp1251"), six.binary_type)
        with self.assertRaises(UnicodeError):
            self.assertIsInstance(ustr(u"Юнікод".encode("cp1251")),
                                  six.text_type)
            self.assertEqual(ustr(u"Юнікод".encode("cp1251")), u"Юнікод")

    def test_ustr_uobj(self):
        ustr = utils.ustr

        self.assertIsInstance(ustr(self.uobj), six.text_type)
        self.assertEqual(ustr(self.uobj), u"Юнікод")

    def test_ustr_bobj(self):
        ustr = utils.ustr

        self.assertIsInstance(ustr(self.bobj), six.text_type)
        self.assertEqual(ustr(self.bobj), u"Юнікод")

    def test_ustr2_unicode(self):
        ustr = self.ustr2

        self.assertIsInstance(ustr(u"Юнікод"), six.text_type)
        self.assertIs(ustr(u"Юнікод"), u"Юнікод")

    def test_ustr2_bytes(self):
        ustr = self.ustr2

        self.assertIsInstance(u"Юнікод".encode("utf-8"), six.binary_type)
        self.assertIsInstance(ustr(u"Юнікод".encode("utf-8")), six.text_type)
        self.assertEqual(ustr(u"Юнікод".encode("utf-8")), u"Юнікод")

    def test_ustr2_bytes_cp1251(self):
        ustr = self.ustr2

        self.assertIsInstance(u"Юнікод".encode("cp1251"), six.binary_type)
        self.assertIsInstance(ustr(u"Юнікод".encode("cp1251")), six.text_type)
        self.assertEqual(ustr(u"Юнікод".encode("cp1251")), u"Юнікод")

    def test_ustr2_uobj(self):
        ustr = self.ustr2

        self.assertIsInstance(ustr(self.uobj), six.text_type)
        self.assertEqual(ustr(self.uobj), u"Юнікод")

    def test_ustr2_bobj(self):
        ustr = self.ustr2

        self.assertIsInstance(ustr(self.bobj), six.text_type)
        self.assertEqual(ustr(self.bobj), u"Юнікод")


class Test_102_Utils_AttrDict(BaseTestCase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.attr_dict = utils.AttrDict(a=42, b=78)

    def test_isinstance(self):
        self.assertIsInstance(self.attr_dict, dict)
        self.assertIsInstance(self.attr_dict, utils.AttrDict)

    def test_getattr(self):
        self.assertIs(self.attr_dict.a, 42)
        self.assertIs(self.attr_dict.b, 78)

        with self.assertRaises(AttributeError):
            self.attr_dict.c

    def test_getitem(self):
        self.assertIs(self.attr_dict['a'], 42)
        self.assertIs(self.attr_dict['b'], 78)

        with self.assertRaises(KeyError):
            self.attr_dict['c']

    def test_dir(self):
        self.assertIn('a', dir(self.attr_dict))
        self.assertIn('b', dir(self.attr_dict))
        self.assertNotIn('c', dir(self.attr_dict))
