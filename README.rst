Odoo RPC Client
===============


.. image:: https://gitlab.com/katyukha/odoo-rpc-client/badges/master/pipeline.svg
    :target: https://gitlab.com/katyukha/odoo-rpc-client/commits/master

.. image:: https://gitlab.com/katyukha/odoo-rpc-client/badges/master/coverage.svg
    :target: https://gitlab.com/katyukha/odoo-rpc-client/commits/master

.. image:: https://img.shields.io/readthedocs/odoo-rpc-client.svg
    :target: https://odoo-rpc-client.readthedocs.io/en/latest/

.. image:: https://img.shields.io/pypi/dm/odoo-rpc-client.svg
    :target: https://pypi.org/project/odoo-rpc-client/
    :alt: PyPI - Downloads

-------------------

.. contents::
   :depth: 2


Canonical source
----------------

The canonical source of *odoo-rpc-client* is hosted on `GitLab <https://gitlab.com/katyukha/odoo-rpc-client>`__.


Overview
--------

This is core part of `OpenERP Proxy <https://github.com/katyukha/openerp-proxy>`__

This project is just **RPC client** for Odoo.
This project provides interface similar to
Odoo internal code to perform operations on **Odoo** objects hiding
**XML-RPC** or **JSON-RPC** behind.


Features
~~~~~~~~

-  *Python 3.5+* support
-  You can call any public method on any OpenERP / Odoo object including:
   *read*, *search*, *write*, *unlink* and others
-  Have *a lot of speed optimizations* (caching, read only requested fields,
   read data for all records in current set (cache), by one RPC call, etc)
-  Desinged to take as more benefits of **IPython autocomplete** as posible
-  Provides *browse\_record* like interface, allowing to browse related
   models too. Supports `browse` method.
   Also adds method `search_records` to simplify
   search-and-read operations.
-  *Extension support*. You can easily modify most of components of this lib
   creating Your own extensions and plugins. It is realy simple. See for examples in
   `openerp_proxy/ext/ <https://github.com/katyukha/openerp-proxy/tree/master/openerp_proxy/ext>`__ directory.
-  *Plugin Support*. Plugins are same as extensions, but aimed to implement additional logic.
   For example look at `odoo_rpc_client/plugins <https://gitlab.com/katyukha/odoo-rpc-client/tree/master/odoo_rpc_client/plugins>`__
   and `odoo_rpc_client/plugin.py <https://gitlab.com/katyukha/odoo-rpc-client/blob/master/odoo_rpc_client/plugin.py>`__ 
-  Support of **JSON-RPC** for *version 8+* of Odoo
-  Support of using **named parametrs** in RPC method calls (server version 6.1 and higher).
-  *Experimental* integration with `AnyField <https://pypi.python.org/pypi/anyfield>`__
-  Missed feature? fill and issue on `GitHub <https://github.com/katyukha/odoo-rpc-client/issues>`__ or `GitLab  <https://gitlab.com/katyukha/odoo-rpc-client/issues>`__


Quick example
~~~~~~~~~~~~~

.. code:: python

    from odoo_rpc_client import Client

    # assume that odoo server is listening localhost on standard 8069 port and
    # have database 'my_db'.
    client = Client('localhost', 'my_db', 'user', 'password')

    # get current user
    client.user
    print(client.user.name)

    # simple rpc calls
    client.execute('res.partner', 'read', [client.user.partner_id.id])

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

Tested with:
- Odoo versions: *10.0*, *11.0*, *12.0*, *13.0*, *14.0*
- Python versions: *2.7*, *3.5*, *3.6*, *3.7*, *3.8*, *3.9*


Install
-------

This project is present on `PyPI <https://pypi.python.org/pypi/odoo_rpc_client/>`__
so it could be installed via PIP::

    pip install odoo_rpc_client

Yodoo Cockpit - Manage your odoo infrastructure via odoo
--------------------------------------------------------

.. image:: https://crnd.pro/web/image/18846/banner_2_4_gif_animation_cut.gif
  :target: https://crnd.pro/yodoo-cockpit
  :alt: Yodoo Cockpit - Manage your odoo infrastructure via odoo

Take a look at `Yodoo Cockpit <https://crnd.pro/yodoo-cockpit>`__ project, and discover the easiest way to manage your odoo installation.
Just short notes about `Yodoo Cockpit <https://crnd.pro/yodoo-cockpit>`__:

- start new production-ready odoo instance in 1-2 minutes.
- add custom addons to your odoo instances in 5-10 minutes.
- out-of-the-box email configuration: just press button and add some records to your DNS, and get a working email
- make your odoo instance available to external world (internet) in 30 seconds (just add single record in your DNS)

If you have any questions, then contact us at `info@crnd.pro <mailto:info@crnd.pro>`__, so we could schedule online-demonstration.

Level up your service quality
-----------------------------

Level up your service with our `Helpdesk <https://crnd.pro/solutions/helpdesk>`__ / `Service Desk <https://crnd.pro/solutions/service-desk>`__ / `ITSM <https://crnd.pro/itsm>`__ solution.

Just test it at `yodoo.systems <https://yodoo.systems/saas/templates>`__: choose template you like, and start working.

Test all available features of `Bureaucrat ITSM <https://crnd.pro/itsm>`__ with `this template <https://yodoo.systems/saas/template/bureaucrat-itsm-demo-data-95>`__.
    

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
`search_records`
or
`read_lecords`
method. Each of these methods receives same aguments as ``search`` or
``read`` method respectively. But passing ``count`` argument for
``search\_records`` will cause error. Main difference betwen these methods
in using `Record` class
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
we start using `extend_me <https://pypi.python.org/pypi/extend_me>`__
library to build extensions and plugins easily.

Plugins are usual classes that provides functionality that should be available
at ``db.plugins.*`` point, implementing logic not related to core system.

--------------

For more information see `source
code <https://gitlab.com/katyukha/odoo-rpc-client>`__ and
`documentation <https://odoo-rpc-client.readthedocs.io/en/latest/>`__
