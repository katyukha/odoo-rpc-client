#!/usr/bin/env python

import os.path
from setuptools import setup, compat

# workaround for: https://github.com/travis-ci/travis-ci/issues/1778
import multiprocessing

# load version info
version_file = os.path.join(os.path.dirname(__file__), 'openerp_proxy', 'version.py')
if compat.PY2:
    execfile(version_file)
elif compat.PY3:
    with open(version_file, 'rb') as f:
        exec(compile(f.read(), version_file, 'exec'))


setup(name='openerp_proxy',
      version=version,
      description='Odoo/OpenERP CLI interface and library for RPC',
      author='Dmytro Katyukha',
      author_email='firemage.dima@gmail.com',
      url='https://github.com/katyukha/openerp-proxy',
      long_description=open('README.rst').read(),
      packages=['openerp_proxy',
                'openerp_proxy.connection',
                'openerp_proxy.service',
                'openerp_proxy.orm',
                'openerp_proxy.ext',
                'openerp_proxy.plugins'],
      scripts=['bin/openerp_proxy'],
      license="GPL",
      classifiers=[
          'Development Status :: 4 - Beta',
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
      keywords=['openerp', 'odoo', 'odoo-rpc', 'rpc', 'xmlrpc',
                'xml-rpc', 'json-rpc', 'jsonrpc', 'odoo-client', 'ipython'],
      extras_require={
          'all': ['ipython[all]'],
      },
      install_requires=[
          'six>=1.9',
          'extend_me>=1.1.3',
          'setuptools>=18',
          'requests>=2.7',
          'ipython>=4',
      ],
      tests_require=[
          'mock',
          'ipython[notebook]',
          'coverage',
      ],
      test_suite='openerp_proxy.tests.all',
)
