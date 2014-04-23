#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='OpenERP Proxy',
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
          'Development Status :: Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: GPL',
          'Programming Language :: Python',
      ],
      keywords=['openerp', 'rpc'],
      extras_require={
          'ipython_shell': ['ipython'],
      }
)
