# -*- coding: utf-8 -*-

import six

from . import BaseTestCase
from .. import utils


class Test_100_Utils(BaseTestCase):

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
