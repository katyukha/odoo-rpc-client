#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='openerp_proxy',
      version='0.1',
      description='OpenERP CLI interface and libraray for RPC',
      author='Dmytro Katyukha',
      author_email='firemage.dima@gmail.com',
      url='https://github.com/katyukha/openerp-proxy',
      long_description=open('README.md').read(),
      packages=['openerp_proxy'],
      scripts=['bin/openerp_proxy'],
      license="GPL",
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: Python',
          'Topic :: Utilities',
          'Topic :: Software Development :: Libraries',
      ],
      keywords=['openerp', 'rpc'],
      extras_require={
          'ipython_shell': ['ipython'],
      }
)
