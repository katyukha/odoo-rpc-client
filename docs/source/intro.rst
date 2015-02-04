OpenERP / Odoo proxy
====================

This project aims to ease access to openerp data via shell and used
mostly for debug purposes. This project provides interface similar to
OpenERP internal code to perform operations on **OpenERP** / **Odoo** object hiding
XML-RPC behind

Overview
--------

Features
~~~~~~~~

-  supports call to all public methods on any OpenERP/Odoo object including:
   *read*, *search*, *write*, *unlink* and others
-  Designed not for speed but to be useful like cli client to OpenERP/Odoo
   (*Versiion 0.5 introduces orm optimizations*)
-  Desinged to take as more benefits of **IPython autocomplete** as posible
-  Also it works good enough in **IPython Notebook** providing **HTML
   representation** for a lot of objects.
-  Ability to display set of records as **HTML Table**
   including **row highlighting**
-  Provides session/history functionality, so if You used it to connect to
   some database before, new connection will be simpler (just enter password).
   Version 0.5 and higher have ability to store passwords. just use
   ``session.option('store_passwords', True); session.save()``
-  Provides *browse\_record* like interface, allowing to browse related
   models too. But use's methods *search\_records* and *browse\_records*
   instead of *browse*. (From version 0.4 *browse* works too)
-  *Extension support*. You can easily modify most of components of this app/lib
   creating Your own extensions. It is realy simple. See for examples in
   openerp_proxy/ext/ directory.
-  *Plugin Support*. Plugins here meant utils, which could store some aditional
   logic, to simplify routine operations.
   Accessible from ``db.plugins.<plugin_name>`` attribute.
-  Support of **JSON-RPC** for *version 8* of OpenERP/Odoo (*experimental*)
-  Support of using **named parametrs** in RPC method calls (server version 6.1 and higher).

-  Missed feature? ask in `Project Issues <https://github.com/katyukha/openerp-proxy/issues>`_


Examples
~~~~~~~~
-  `Examples & HTML tests <http://nbviewer.ipython.org/github/katyukha/openerp-proxy/blob/master/examples/Examples%20&%20HTML%20tests.ipynb>`_


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
   object, and record levels.  **DONE**
-  Django-like search API implemented as extension
    - Something like ``F`` or ``Q`` expressions from Django
    - to make working constructions like:
      ``object.filter((F('price') > 100.0) & (F('price') != F('Price2')))``


Install
-------

To install package just use PIP::

    pip install openerp_proxy
    
this will make available package *openerp\_proxy* and also shell will be available by
command ``$ openerp_proxy``

If You want to install development version of *OpenERP Proxy* you can do it via::

    pip install -e git+https://github.com/katyukha/openerp-proxy.git#egg=openerp_proxy


Also if You plan to use this project as shell client, it is recommended to install IPython
and If You  would like to have ability to play with Odoo / OpenERP data in IPython notebook,
it is recommended to also install IPython's Notebook support. To install IPython and IPython Notebook
just type::

    pip install ipython ipython[notebook]


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

So here is a way to create connection

::

    import openerp_proxy.core as oe_core
    db = oe_core.ERP_Proxy(dbname='my_db',
                           host='my_host.int',
                           user='my_db_user',
                           pwd='my_password here')

And next all there same, no more differences betwen shell and lib usage.


Use in IPython's notebook
-------------------------

To better suit for HTML capable notebook You would like to use IPython's version of *session*
object and *openerp_proxy.ext.repr* extension.
So in first cell of notebook import session and extensions/plugins You want::

    from openerp_proxy.session import IPYSession as Session  # Use IPython-itegrated session class
    import openerp_proxy.ext.repr              # Enable representation extension. This provides HTML representation of objects
    from openerp_proxy.ext.repr import HField  # Used in .as_html_table method of RecordList

    session = Session()

Now most things same as for shell usage, but...
In some versions of IPython's notebook not patched version of *getpass* func/module,
so if You not provide password when getting database (*connect*, *get_db* methods, You would be asked
for it, but this prompt will be displayed in shell where notebook server is running, not on webpage.
To solve this, it is recommended to uses *store_passwords* option::
    
    session.option('store_passwords', True)
    session.save()

In this way, only when You connect first time, You need to explicitly pass password to *connect* of *get_db* methods.

(*do not forget to save session, after new connection*)


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
in using *Record* class instead of *dict* for each record had been
read. Record class provides some orm-like abilities for records,
allowing for example access fields as attributes and provide mechanisms
to lazily fetch related fields.

::

    >>> sale_orders = sale_order_obj.search_records([('state', '=', 'done')])
    >>> sale_orders[0]
    ... R(sale.order, 9)[SO0011]
    >>>
    >>> # So we have list of Record objects. Let's check what they are
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


Start-up imports
----------------

If You want some modules (extensions/plugins) to be automatiacly loaded/imported
at start-up, there are ``session.start_up_imports`` property, that points to 
list that holds names of movedule to be imported at start-up.

For example, if You want *Sugar extension* to be automaticaly imported, just
add it to ``session.start_up_imports`` list

::

    session.start_up_imports.append('openerp_proxy.ext.sugar')

After this, when You will start new openerp_proxy shell, *sugar extension*
will be automaticaly enable.


Plugins
-------

In version 0.4 plugin system was completly refactored. At this version
we start using *extend_me* library to build extensions and plugins.

Plugins are usual classes that provides functionality that should be available
at ``db.plugins.*`` point, implementing logic not related to core system.

To ilustrate what is plugins and what they can do we will create one.
So let's start

1. create some directory to place plugins in:
   
   ``mkdir ~/oerp_proxy_plugins/``
   
   ``cd ~/oerp_proxy_plugins/``

2. next create simple file called ``attendance.py`` and edit it
   
   ``vim attendance.py``

3. write folowing code there

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

4. Now Your plugin is done. Let's test it.
   Run ``openerp_proxy`` and try to import it

    ::

        >>> # First add path of Your plugin to session.
        >>> # When session is started all registered paths 
        >>> # will be automaticaly added to sys.path.
        >>> # If You do not want this behavior,
        >>> # use standard 'sys.path.append(path)'
        >>> session.add_path('~/oerp_proxy_plugins/')

        >>> # and import our plugin
        >>> import attendance

        >>> # and use it
        >>> db = session.connect()
        >>> db.plugin.attendance.get_sign_state()
        'present'

        >>> # If You want some plugins or extensions or other
        >>> # modules imported at start-up of session, do this
        >>> session.start_up_imports.add('attendance')

As You see above, to use plugin (or extension), just import it module (better at startu-up)

--------------

For more information see `source
code <https://github.com/katyukha/openerp-proxy>`_ or
`documentation <http://pythonhosted.org//openerp_proxy/>`_.


Alternatives
~~~~~~~~~~~~

-  `Official OpenERP client
   library <https://github.com/OpenERP/openerp-client-lib>`_
-  `ERPpeek <https://pypi.python.org/pypi/ERPpeek>`_
-  `OEERPLib <https://pypi.python.org/pypi/OERPLib>`_

