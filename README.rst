OpenERP / Odoo proxy
====================


.. image:: https://travis-ci.org/katyukha/openerp-proxy.svg?branch=master
    :target: https://travis-ci.org/katyukha/openerp-proxy

.. image:: https://coveralls.io/repos/katyukha/openerp-proxy/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/katyukha/openerp-proxy?branch=master
    
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

This project is just **RPC client** for Odoo.
It aims to ease access to openerp data via shell and used
mostly for data debuging purposes. This project provides interface similar to
Odoo internal code to perform operations on **OpenERP** / **Odoo** objects hiding
**XML-RPC** or **JSON-RPC** behind.


    - Are You still using pgAdmin for quering Odoo database?
    - Try this package (especialy with IPython Notebook), and You will forget about pgAdmin!


Features
~~~~~~~~

-  *Python 3.3+* support
-  You can call any public method on any OpenERP / Odoo object including:
   *read*, *search*, *write*, *unlink* and others
-  Have *a lot of speed optimizations* (caching, read only fields accessed,
   read data for all records in current set, by one RPC call, etc)
-  Desinged to take as more benefits of **IPython autocomplete** as posible
-  Works nice in **IPython Notebook** providing **HTML
   representation** for a most of objects.
-  Ability to export HTML table recordlist representation to *CSV file*
-  Ability to save connections to different databases in session.
   (By default password is not saved, and will be asked, but if You need to save it, just do this:
   ``session.option('store_passwords', True); session.save()``)
-  Provides *browse\_record* like interface, allowing to browse related
   models too. Supports *browse* method. Also adds method *search\_records* to simplify
   search-and-read operations.
-  *Extension support*. You can easily modify most of components of this app/lib
   creating Your own extensions and plugins. It is realy simple. See for examples in
   openerp_proxy/ext/ directory.
-  *Plugin Support*. Plugins are same as extensions, but aimed to implement additional logic.
   For example look at *openerp_proxy/plugins* and *openerp_proxy/plugin.py* 
-  Support of **JSON-RPC** for *version 8+* of Odoo
-  Support of using **named parametrs** in RPC method calls (server version 6.1 and higher).
-  *Sugar extension* which simplifys code a lot.

-  Missed feature? ask in `Project Issues <https://github.com/katyukha/openerp-proxy/issues>`_


Quick example
~~~~~~~~~~~~~

::

    from openerp_proxy import Client

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
        print("-"*5)
        print()


Supported Odoo server versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tested with Odoo 7.0, 8.0, 9.0

Also shoud work with Odoo 6.1

Also it should work with Odoo version 6.0, except the things related to passing named parametrs
to server methods, such as using context in ``openerp_proxy.orm`` package


Examples
~~~~~~~~

-  `Examples & HTML tests <http://nbviewer.ipython.org/github/katyukha/openerp-proxy/blob/master/examples/Examples%20&%20HTML%20tests.ipynb>`_


Install
-------

This project is present on `PyPI <https://pypi.python.org/pypi/openerp_proxy/>`_
do it could be installed via PIP::

    pip install openerp_proxy
    
this will make available package *openerp\_proxy* and also shell will be available by
command ``$ openerp_proxy``

If You want to install development version of *OpenERP Proxy* you can do it via::

    pip install -e git+https://github.com/katyukha/openerp-proxy.git#egg=openerp_proxy


Also if You plan to use this project as shell client, it is **recommended to install IPython**
and If You  would like to have ability to play with Odoo data in IPython notebook,
it is recommended to also install IPython's Notebook support. To install IPython and IPython Notebook
just type::

    pip install ipython ipython[notebook]


Usage
-----

Use as shell
~~~~~~~~~~~~

After instalation run in shell:

::

       openerp_proxy

And You will get the openerp_proxy shell. If *IPython* is installed then IPython shell
will be used, else usual python shell will be used. There is in context exists
*session* variable that represents current session to work with

Next You have to get connection to some Odoo database.

::

    >>> db = session.connect()

This will ask You for host, port, database, etc to connect to and return Client instance
which represents database connection.


Use as library
~~~~~~~~~~~~~~

The one diference betwen using as lib and using as shell is the way
connection to database is created. When using as shell the primary object
is session, which provides some interactivity. But when using as library
in most cases there are no need for that interactivity, so connection
should be created manualy, providing connection data from some other sources
like config file or something else.

So here is a way to create connection

::

    from openerp_proxy.core import Client
    db = Client(host='my_host.int',
                dbname='my_db',
                user='my_db_user',
                pwd='my_password here')

And next all there same, no more differences betwen shell and lib usage.


Use in IPython's notebook
~~~~~~~~~~~~~~~~~~~~~~~~~

To better suit for HTML capable notebook You would like to use IPython's version of *session*
object and *openerp_proxy.ext.repr* extension.
So in first cell of notebook import session and extensions/plugins You want::

    # also You may import all standard extensions in one line:
    from openerp_proxy.ext.all import *

    # note that extensions were imported before session,
    # because some of them modify Session class
    from openerp_proxy.session import Session
    from openerp_proxy.core import Client

    session = Session()

Now most things same as for shell usage, but...
In some versions of IPython's notebook not patched version of *getpass* func/module,
so if You not provide password when getting database (*connect*, *get_db* methods, You would be asked
for it, but this prompt will be displayed in shell where notebook server is running, not on webpage.
To solve this, it is recommended to uses *store_passwords* option::
    
    session.option('store_passwords', True)
    session.save()

Next use it like shell, but *do not forget to save session, after new connection*::

    db = session.connect()
    session.save()
    
or like lib::

    db = Client(host='my_host.int',
                dbname='my_db',
                user='my_db_user',
                pwd='my_password here')

*Note*: in old version of IPython getpass was not work correctly,
so maybe You will need to pass password directly to *session.connect* method.


General usage
~~~~~~~~~~~~~

For example lets try to find how many sale orders in 'done' state we have in
our database. (Look above sections to get help on how to connect to Odoo database)

::

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
in using *Record* class instead of *dict* for each record had been
read. Record class provides some orm-like abilities for records,
allowing for example access fields as attributes and provide mechanisms
to lazily fetch related fields.

::

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

Session: db aliases
~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~

This extension provides some syntax sugar to ease access to objects

So to start use it just import this extension **just after start**

::

    import openerp_proxy.ext.sugar

And after that You will have folowing features working

::

    db['sale.order'][5]       # fetches sale order with ID=5
    db['sale_order']('0050')  # result in name_search for '0050' on sale order
                              # result may be Record if one record found
                              # or RecordList if there some set of records found
    db['sale.order']([('state','=','done')])    # Same as 'search_records' method
    db['sale.order'](state='done')              # simplified search

    # Automatic object aliaces. Also supports autocompletition
    # via implementation of __dir__ method
    db._sale_order == db['sale.order'] == db['sale_order']   # => True


For other extensions look at *openerp_proxy/ext* subdirectory


Session: Start-up imports
~~~~~~~~~~~~~~~~~~~~~~~~~

If You want some modules (extensions/plugins) to be automatiacly loaded/imported
at start-up, there are ``session.start_up_imports`` property, that points to 
list that holds names of modules to be imported at session creation time.

For example, if You want *Sugar extension* to be automaticaly imported, just
add it to ``session.start_up_imports`` list

::

    session.start_up_imports.append('openerp_proxy.ext.sugar')

After this, when You will start new openerp_proxy shell, *sugar extension*
will be automaticaly enable.


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
                emp_obj = self.proxy['hr.employee']
                emp_id = emp_obj.search([('user_id', '=', self.proxy.uid)])
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
code <https://github.com/katyukha/openerp-proxy>`_ or
`documentation <http://pythonhosted.org//openerp_proxy/>`_.
