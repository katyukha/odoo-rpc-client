OpenERP/Odoo proxy
=============

This project aims to ease access to openerp data via shell and used
mostly for debug purposes. This project provides interface similar to
OpenERP internal code to perform operations on OpenERP/Odoo object hiding
XML-RPC behind

Overview
--------

Features
~~~~~~~~

-  supports call to all public methods on any OpenERP/Odoo object including:
   *read*, *search*, *write*, *unlink* and others
-  Designed not for speed but to be useful like cli client to OpenERP/Odoo
-  Desinged to take as more benefits of *IPython autocomplete* as posible
-  Provides session/history functionality, so if You used it to connect to
   some database before, new connection will be simpler (just enter password).
-  Provides *browse\_record* like interface, allowing to browse related
   models too. But use's methods *search\_records* and *browse\_records*
   instead of *browse*
-  *Extension support*. You can modify most of components of this app/lib
   creating Your own extensions. It is realy simple. See for examples in
   openerp_proxy/ext/ directory.
-  *Plugin Support*. You can write Your scripts that uses this lib,
   and easily use them from session. no packages for them required,
   just tell the path where script file is placed
-  Support of JSON-RPC for version 8 of OpenERP (experimental)

What You can do with this
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Quickly read and analyze some data that is not visible in interface
   without access to DB
-  Use this project as library for code that need to access OpenERP data
-  Use in scripts that migrates OpenERP data (after, for example, adding
   new functionality or changing old). (Migration using only SQL is bad
   idea because of functional fields with *store=True* which must be
   recalculated).

Near future plans
~~~~~~~~~~~~~~~~~

-  Better plugin system which will allow to extend API on database,
   object, and record levels
-  Django-like search and write API implemented as extension


Install
-------

Install package with ``pip install openerp_proxy``, this will make
available package *openerp\_proxy* and also shell will be available by
command ``$ openerp_proxy``

If You want to install development version of *OpenERP Proxy* you can
do it via ``pip install -e git+https://github.com/katyukha/openerp-proxy.git#egg=openerp_proxy``


Use as shell
------------

After instalation run in shell:

::

       openerp_proxy

And You will get the openerp_proxy shell. If *IPython* is installed then IPython shell
will be used, else usual python shell will be used. There is in context exists
*session* variable that represents current session to work with

Next You have to get connection to some OpenERP/Odoo database.

::

    >>> db = session.connect()

This will ask You for host, port, database, etc to connect to. Now You
have connection to OpenERP database which allows You to use database
objects.


Use as library
--------------

The one diference betwen using as lib and using as shell is the way
connection to database is created. When using as shell the primary object
is session, which provides some interactivity. But when using as library
in most cases there are no need for that interactivity, so connection
should be created manualy, providing connection data from some other sources
like config file or something else.

So here is a way to create connection:

::
    import openerp_proxy.core as oe_core
    db = oe_core.ERP_Proxy(dbname='my_db', host='my_host.int',user='my_db_user', pwd='my_password here')

And next all there same, no more differences betwen shell and lib usage.


General usage
-------------

Lets try to find how many sale orders in 'done' state we have in
database:

::

    >>> sale_order_obj = db['sale.order']  # or You may use 'db.get_obj('sale.order')' if You like
    >>>
    >>> # Now lets search for sale orders:
    >>> sale_order_obj.search([('state', '=', 'done')], count=True)
    >>> 5

So we have 5 orders in done state. So let's read them.

Default way to read data from OpenERP is to search for required records
with *search* method which return's list of IDs of records, then read
data using *read* method. Both methods mostly same as OpenERP internal
ones:

::

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

Another way to read data is to use *search\_records* or *read\_records*
method. Each of these methods receives same aguments as *search* or
*read* method respectively. But passing *count* argument for
*search\_records* will cause error. Main difference betwen these methods
in using *ERP\_Record* class instead of *dict* for each record had been
read. ERP\_Record class provides some orm-like abilities for records,
allowing for example access fields as attributes and provide mechanisms
to lazily fetch related fields.

::

    >>> sale_orders = sale_order_obj.search_records([('state', '=', 'done')])
    >>> sale_orders[0]
    ... R(sale.order, 9)[SO0011]
    >>>
    >>> # So we have list of ERP_Record objects. Let's check what they are
    >>> so = sale_orders[0]
    >>> so.id
    ... 9
    >>> so.name
    ... SO0011
    >>> so.partner_id 
    ... R(res.partner, 9)[Better Corp]
    >>>
    >>> so.partner_id.name
    ... Better Corp
    >>> so.partner_id.active
    ... True


Session: db aliases
-------------------

Session provides ability to add aliases to databases, which will simplify access to them.
To add aliase to our db do the folowing:

::
    >>> session.aliase('my_db', db)
    
And now to access this database in future (even after restart)
You can use next code

::
    >>> db = session.my_db

this allows to faster get connection to database Your with which You are working very often


Sugar extension
---------------

This extension provides some syntax sugar to ease access to objects

So to start use it just import this extension **just after start**

::
    import openerp_proxy.sugar

And after that You will have folowing features working

::
    db['sale.order'][5]       # fetches sale order with ID=5
    db['sale_order']('0050')  # result in name_search for '0050' on sale order
                              # result may be Record if one record found
                              # or RecordList if there some set of records found

For other extensions look at *openerp_proxy/ext* subdirectory

Plugins
-------

Plugins are separate scripts that could be placed anywhere on file
system. Plugin shoud be python file or package which colud be imported
and with specific structure So to define new plugin just place next code
on some where You would like to store plugin code.

::

    # Plugis just provides some set of classes and functions which could do some predefined work
    class MyPluginClass(object):
        _name = 'my_class1'  # Name of class placed in plugin

        # Init must receive 'db' argement which is ERP_Proxy instace
        # Plugin system is lazy, so all classes or even plugins at all will be initialized
        # only when some code requestes for them trying to access it.
        def __init__(self, db):
            self.db = db  # Save database instance to be able to work with data letter

        # Define methods You would  like to provide to end user
        def my_cool_method(self, arg1, argN):
            # Do some work

    # And define initialization method for plugin which will show what this plugin provides to user
    def plugin_init():
        return {
            'classes': MyPluginClass,
            'name': 'my_plugin',
        }

And now to use this plugin just load it to session:

::

    >>> session.load_plugin("<path to your plugin>")  # this may be called in any place of code.
    >>> db = session.connect()
    >>> db.plugins.my_plugin.my_class1.my_cool_method()

--------------

For more information see `source
code <https://github.com/katyukha/openerp-proxy>`_.


Alternatives
~~~~~~~~~~~~

-  `Official OpenERP client
   library <https://github.com/OpenERP/openerp-client-lib>`_
-  `ERPpeek <https://pypi.python.org/pypi/ERPpeek>`_
-  `OEERPLib <https://pypi.python.org/pypi/OERPLib>`_

