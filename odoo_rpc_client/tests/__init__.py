import os
import six
import unittest
from ..utils import AttrDict

import logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


# Python 2/3 compatability
try:
    import unittest.mock as mock
except ImportError:
    import mock

__all__ = ('BaseTestCase', 'mock')


class BaseTestCase(unittest.TestCase):
    """Instanciates an ``odoorpc.ODOO`` object, nothing more."""
    def setUp(self):
        try:
            port = int(os.environ.get('ODOO_TEST_PORT', 8069))
        except ValueError:
            raise ValueError("The port must be an integer")

        self.env = AttrDict({
            'protocol': os.environ.get('ODOO_TEST_PROTOCOL', 'xml-rpc'),
            'host': os.environ.get('ODOO_TEST_HOST', 'localhost'),
            'port': port,
            'dbname': os.environ.get('ODOO_TEST_DB',
                                     'odoo_rpc_client_test_db'),
            'user': os.environ.get('ODOO_TEST_USER', 'admin'),
            'password': os.environ.get('ODOO_TEST_PASSWORD', 'admin'),
            'super_password': os.environ.get('ODOO_TEST_SUPER_PASSWORD',
                                             'admin'),
        })

        self.test_db_service = os.environ.get('TEST_DB_SERVICE', False)
        self.recreate_db = os.environ.get('RECREATE_DB', False)

    if six.PY3:
        def assertItemsEqual(self, *args, **kwargs):
            return self.assertCountEqual(*args, **kwargs)
