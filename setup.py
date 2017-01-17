#!/usr/bin/env python

import os.path
import sys
from setuptools import setup

# workaround for: https://github.com/travis-ci/travis-ci/issues/1778
import multiprocessing  # noqa

# load version info
version_file = os.path.join(os.path.dirname(__file__),
                            'odoo_rpc_client',
                            'version.py')
readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')

if sys.version_info < (3,):
    execfile(version_file)
else:
    with open(version_file, 'rb') as f:
        exec(compile(f.read(), version_file, 'exec'))


setup(name='odoo_rpc_client',
      version=version,
      description='Odoo/OpenERP library for RPC',
      author='Dmytro Katyukha',
      author_email='firemage.dima@gmail.com',
      url='https://github.com/katyukha/odoo-rpc-client',
      long_description=open(readme_file).read(),
      packages=['odoo_rpc_client',
                'odoo_rpc_client.connection',
                'odoo_rpc_client.service',
                'odoo_rpc_client.orm',
                'odoo_rpc_client.tests',
                'odoo_rpc_client.plugins',
                ],
      license="GPL",
      classifiers=[
          'Development Status :: 3 - Alpha',
          # 'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Utilities',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords=['odoo', 'odoo-rpc', 'rpc', 'xmlrpc',
                'xml-rpc', 'json-rpc', 'jsonrpc', 'odoo-client', 'openerp'],
      extras_require={
          'all': ['anyfield'],
      },
      install_requires=[
          'six>=1.10',
          'extend_me>=1.1.3',
          'setuptools>=18',
          'requests>=2.7',
      ],
      tests_require=[
          'mock',
          'coverage',
          'anyfield',
      ],
      test_suite='odoo_rpc_client.tests.all',
)
