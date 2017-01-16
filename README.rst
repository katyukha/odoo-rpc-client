OpenERP / Odoo proxy
====================


.. image:: https://travis-ci.org/katyukha/odoo-rpc-client.svg?branch=master
    :target: https://travis-ci.org/katyukha/odoo-rpc-client

.. image:: https://coveralls.io/repos/github/katyukha/odoo-rpc-client/badge.svg?branch=master
 :target: https://coveralls.io/github/katyukha/odoo-rpc-client?branch=master


..
    .. image:: https://img.shields.io/pypi/v/openerp_proxy.svg
        :target: https://pypi.python.org/pypi/openerp_proxy/
    .. image:: https://img.shields.io/pypi/l/openerp_proxy.svg
        :target: https://pypi.python.org/pypi/openerp_proxy/
    .. image:: https://img.shields.io/pypi/pyversions/openerp_proxy.svg
        :target: https://pypi.python.org/pypi/openerp_proxy/
    .. image:: https://img.shields.io/pypi/format/openerp_proxy.svg
        :target: https://pypi.python.org/pypi/openerp_proxy/

-------------------

.. contents::
   :depth: 2


Overview
--------

This is core part of `OpenERP Proxy <https://github.com/katyukha/openerp-proxy>`__

This project is just **RPC client** for Odoo.
This project provides interface similar to
Odoo internal code to perform operations on **OpenERP** / **Odoo** objects hiding
**XML-RPC** or **JSON-RPC** behind.


***Note***: documentation now is "Work in Progress" state, so here is documentation from openerp_proxy project.
in most cases it compatible, except extensions, which are not in this project.



Features
~~~~~~~~

-  *Python 3.3+* support
-  You can call any public method on any OpenERP / Odoo object including:
   *read*, *search*, *write*, *unlink* and others
-  Have *a lot of speed optimizations* (caching, read only requested fields,
   read data for all records in current set (cache), by one RPC call, etc)
-  Desinged to take as more benefits of **IPython autocomplete** as posible
-  Provides *browse\_record* like interface, allowing to browse related
   models too. Supports `browse <http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.orm.html#openerp_proxy.orm.record.ObjectRecords.browse>`__ method.
   Also adds method `search_records <http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.orm.html#openerp_proxy.orm.record.ObjectRecords.search_records>`__ to simplify
   search-and-read operations.
-  *Extension support*. You can easily modify most of components of this app/lib
   creating Your own extensions and plugins. It is realy simple. See for examples in
   `openerp_proxy/ext/ <https://github.com/katyukha/openerp-proxy/tree/master/openerp_proxy/ext>`__ directory.
-  *Plugin Support*. Plugins are same as extensions, but aimed to implement additional logic.
   For example look at `openerp_proxy/plugins <https://github.com/katyukha/openerp-proxy/tree/master/openerp_proxy/plugins>`__
   and `openerp_proxy/plugin.py <https://github.com/katyukha/openerp-proxy/blob/master/openerp_proxy/plugin.py>`__ 
-  Support of **JSON-RPC** for *version 8+* of Odoo
-  Support of using **named parametrs** in RPC method calls (server version 6.1 and higher).
-  *Experimental* integration with `AnyField <https://pypi.python.org/pypi/anyfield>`__

-  Missed feature? ask in `Project Issues <https://github.com/katyukha/odoo-rpc-client/issues>`__


Quick example
~~~~~~~~~~~~~

.. code:: python

    from odoo_rpc_client import Client

    client = Client('localhost', 'my_db', 'user', 'password')

    # get current user
    client.user
    print(user.name)

    # simple rpc calls
    client.execute('res.partner', 'read', [user.partner_id.id])

    # Model browsing
    SaleOrder = client['sale.order']
    s_orders = SaleOrder.search_records([])
    for order in s_orders:
        print(order.name)
        for line in order.order_line:
            print("\t%s" % line.name)
        print("-" * 5)
        print()


Supported Odoo server versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tested with Odoo *7.0*, *8.0*, *9.0*, *10.0rc1c*

Also shoud work with Odoo 6.1


Examples
~~~~~~~~

-  `Basics <http://nbviewer.ipython.org/github/katyukha/openerp-proxy/blob/master/examples/Basics.ipynb>`_
-  `Examples & HTML tests <http://nbviewer.ipython.org/github/katyukha/openerp-proxy/blob/master/examples/Examples%20&%20HTML%20tests.ipynb>`_
-  `RecordList Representation <http://nbviewer.ipython.org/github/katyukha/openerp-proxy/blob/master/examples/RecordList%20Representation.ipynb>`_


Install
-------

This project is present on `PyPI <https://pypi.python.org/pypi/odoo_rpc_client/>`_
so it could be installed via PIP::

    pip install odoo_rpc_client
    

Usage
-----

Connect to server / database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The one diference betwen using as lib and using as shell is the way
connection to database is created. When using as shell the primary object
is session, which provides some interactivity. But when using as library
in most cases there are no need for that interactivity, so connection
should be created manualy, providing connection data from some other sources
like config file or something else.

So here is a way to create connection

.. code:: python

    from odoo_rpc_client import Client
    db = Client(host='my_host.int',
                dbname='my_db',
                user='my_db_user',
                pwd='my_password here')

And next all there same, no more differences betwen shell and lib usage.


General usage
~~~~~~~~~~~~~

For example lets try to find how many sale orders in 'done' state we have in
our database. (Look above sections to get help on how to connect to Odoo database)

.. code:: python

    >>> sale_order_obj = db['sale.order']  # or You may use 'db.get_obj('sale.order')' if You like
    >>>
    >>> # Now lets search for sale orders:
    >>> sale_order_obj.search([('state', '=', 'done')], count=True)
    5

So we have 5 orders in done state. So let's read them.

Default way to read data from Odoo is to search for required records
with *search* method which return's list of IDs of records, then read
data using *read* method. Both methods mostly same as Odoo internal
ones:

.. code:: python

    >>> sale_order_ids = sale_order_obj.search([('state', '=', 'done')])
    >>> sale_order_datas = sale_order_obj.read(sale_order_ids, ['name'])  # Last argument is optional.
                                                                          # it describes list of fields to read
                                                                          # if it is not provided then all fields
                                                                          # will be read
    >>> sale_order_datas[0]
    {'id': 3,
     'name': 'SO0004'
    }

As we see reading data in such way allows us to get list of dictionaries
where each contain fields have been read

Another way to read data is to use
`search_records <http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.orm.html#openerp_proxy.orm.record.ObjectRecords.search_records>`_
or
`read_records <http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.orm.html#openerp_proxy.orm.record.ObjectRecords.read_records>`_
method. Each of these methods receives same aguments as ``search`` or
``read`` method respectively. But passing ``count`` argument for
``search\_records`` will cause error. Main difference betwen these methods
in using `Record <http://pythonhosted.org/openerp_proxy/module_ref/openerp_proxy.orm.html#openerp_proxy.orm.record.Record>`_ class
instead of *dict* for each record had been read. Record class provides some orm-like abilities for records,
allowing for example access fields as attributes and provide mechanisms
to lazily fetch related fields.

.. code:: python

    >>> sale_orders = sale_order_obj.search_records([('state', '=', 'done')])
    >>> sale_orders[0]
    R(sale.order, 9)[SO0011]
    >>>
    >>> # So we have list of Record objects. Let's check what they are
    >>> so = sale_orders[0]
    >>> so.id
    9
    >>> so.name
    SO0011
    >>> so.partner_id 
    R(res.partner, 9)[Better Corp]
    >>>
    >>> so.partner_id.name
    Better Corp
    >>> so.partner_id.active
    True


Additional features
-------------------

Plugins
~~~~~~~

In version 0.4 plugin system was completly refactored. At this version
we start using `extend_me <https://pypi.python.org/pypi/extend_me>`_
library to build extensions and plugins easily.

Plugins are usual classes that provides functionality that should be available
at ``db.plugins.*`` point, implementing logic not related to core system.

To ilustrate what is plugins and what they can do we will create a simplest one.
So let's start

1. create some directory to place plugins in:
   
   ``mkdir ~/oerp_proxy_plugins/``
   
   ``cd ~/oerp_proxy_plugins/``

2. next create simple file called ``attendance.py`` and edit it
   
   ``vim attendance.py``

3. write folowing code there (note that this example works and tested for Odoo version 6.0 only)

    ::

        from openerp_proxy.plugin import Plugin

        class AttandanceUtils(Plugin):

            # This is required to register Your plugin
            # *name* - is for db.plugins.<name>
            class Meta:
                name = "attendance"

            def get_sign_state(self):
                # Note: folowing code works on version 6 of Openerp/Odoo
                emp_obj = self.client['hr.employee']
                emp_id = emp_obj.search([('user_id', '=', self.client.uid)])
                emp = emp_obj.read(emp_id, ['state'])
                return emp[0]['state']
                
4. Now your plugin is completed, but it is not on python path.
   There is ability to add additional paths to session, so
   when session starts, ``sys.path`` will be patched with that paths.
   To add your extra path to session You need do folowing::
   
       >>> session.add_path('~/oerp_proxy_plugins/')
       >>> session.save()
       
   Now, each time session created, this path will be added to python path

5. Now we cat test our plugin.
   Run ``openerp_proxy`` and try to import it::

        >>> #import our plugin
        >>> import attendance

        >>> # and use it
        >>> db = session.connect()
        >>> db.plugin.attendance.get_sign_state()
        'present'

        >>> # If You want some plugins or extensions or other
        >>> # modules imported at start-up of session, do this
        >>> session.start_up_imports.add('attendance')

As You see above, to use plugin (or extension), just import it's module (better at startu-up)

--------------

For more information see `source
code <https://github.com/katyukha/odoo-rpc-client>`_ or
`documentation <http://pythonhosted.org/openerp_proxy/>`__.
