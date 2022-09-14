Last changes
============

Release 1.2.0
-------------

- Fix regression with SSL support for XML-RPC.
  Still, it is recommended to use JSON-RPC, because it is more reliable.
- Added auto tests for Odoo 15.0 and python 3.10

Release 1.1.0
-------------

- Added support (tests) of Odoo 13.0, Odoo 14.0 and python3.8
- Added tests for batch create in Odoo 12.0+
- Support for Odoo 7.0 is now deprecated and will be completely removed in one
  of next versions
- Odoo 8.0 and 9.0 now supported, but not tested.

Release 1.0.0
-------------

- Support for timeout in connections
- Changed license to `MPL 2.0 <http://mozilla.org/MPL/2.0/>`__


Release 0.9.0
-------------

- Removed old alias *odoo_rpc_client.orm.record.RecordRelations
- Added *search_count* method to objects (models)
- Added *create_record* method to objects (models)
- Added tests for Odoo 11
- Added overloads of operators (+, +=) for recordlists
- Removed *local* database connector, because it is difficult to test it,
  and it is not used so often as *xml-rpc* and *json-rpc* connectors
  May be in future it will have it's own python package.


Release 0.8.2
-------------

- Avoid unneccesary encode/decode in db dump/restore logic
- Use simplejson for jsonrpc
- Odoo 10 local connector: correcly close db connections on exit


Release 0.8.1
-------------

- Fix local connector for odoo-9.0 when odoo.py is on python path


Big split: odoo_rpc_client 0.8.0
--------------------------------

- Split openerp_proxy project to set of smaler project
  to avoid bringing lot of unneccessary dependencies.
- This project contains core features, aiming to minimize dependencies.
- Features, not included here, all this features will be still available
  in openerp_proxy project, which will depend on this one in future:
    - Extensions (especialy repr extension)
    - Sessions
    - Shell
    - Experimental code (introduced in openerp_proxy 0.7.0)
    - Plugin - Diagraming
- New features added:
    - Connector: 'local'. It allows to connect to local odoo instalce,
                 without http;

Release 0.7.1
-------------

- Bugfix in ``Client.ref`` method. now it returns ``Record`` instance,
  as mentioned in documentation
- Added ``Record.get(field_name, default)`` method.

Release 0.7.0
-------------

- ``client.server_version`` now is aliase to
  ``client.services.db.server_base_version``
- Added ``services.db.server_base_version()`` which could be safely compared like:
  ``client.services.db.server_base_version() >= pkg_resources.parse_version('9.0')``
- Added method ``search_read`` to orm.object
- Drop support of OpenERP 6.0
- ``ext.repr``: Added ability to pass table format to .as_table method
  tablefmt arg must be suitable for tabulate.tabulate method from
  `Tabulate <https://pypi.python.org/pypi/tabulate>`__ package
- Added ``openerp_proxy.experimental`` subpackage.
- Refactored session logic. Logic related to database / client connection
  management moved to separate class ``openerp_proxy.session.ClientManager``
  which can be used outside session logic.
- Added ``Client.ref`` method, then returns ``Record`` instance for
  specified *xmlid*
- Added ``Client.database_version_full`` and ``Client.database_version``
  properties
- Added ``Session.del_db`` and ``ClientManager.del_client`` methods
- Added ``client.services.db.db_exist`` method wrapper

Release 0.6.9
-------------

- ``external_ids`` plugin now adds ``Record.as_xmlid`` method
- bugfix: ensure thet record is present in cache on init of Record class
- bugfix: [json-rpc], if RPC method results in None, then there is no
  'result' object in response, so if there are no 'error' object, nor 'result',
  then suppose that 'result' is None, thus it is possible to deal with
  Odoo methods, that returns None as result via RPC


Release 0.6.8
-------------

- bugfix in ``HTMLTable.to_csv`` for Python 3
  related to writing non-ascii characters to csv file
- Link to new example added to readme
- session added property ``index_rev``, which is used
  to save index in file
- bugfix in ``utils.AttrDict.__dir__`` method.
  now it works, so IPython auto-comlete for
  objects that use ``utils.AttrDict`` class works too
- better support of last IPython shell
- prefetching:
   - bugfix: some times when passed few fields with
     same names, prefetch raises strange errors
     (atleast on odoo 7.0 instance)
   - improvement: prefetch only records that
     have no at least one field in cache


Release 0.6.7
-------------

- Representation module improvements
    - HField: added ``is_header`` parameter, which in HTML representation
      wraps field in ``<th>`` tag instead of default ``<td>``
    - ``orm.Record`` representation improvement:
      now it is displayed as three-column table with
      system field name, user visible field name and field value
- Examples:
    - Added one more example:
      `RecordList Representation.ipynb <examples/RecordList Representation.ipynb>`__
- Bugfixes:
    - session: client._no_save attr was not set on client by default
    - session: connection index now saved in session too
    - representation: better handled cases when HField._field is callable
      which throws error,
      now, if field._silent is set, then no error will be raised
    - representation: if HField which results in HTML capable value,
      displayed not inside HTMLTable, then default value representation
      will be used, not HTML one.

        
Release 0.6.6
-------------

- Bugfix: Issue `#4 <https://github.com/katyukha/openerp-proxy/issues/4>`__
- Bugfix: double call to _get_registered_objects, caused be cleaning caches,
  on assess to any service first time
- module_utils plugin fixes mostly related to __dir__ method
  (used for auto-complete in IPython)

    - added ``stdcall`` decorators to ``upgrade`` and ``install``
      methods of 'ir.module.module' object
    - Bugfix in ``__dir__`` implementation for plugin object
    - added ``installed_modules`` property to ``module_utils`` plugin
    - better tests for this plugin


Release 0.6.5
-------------

- Added ``openerp_proxy.plugins.external_ids`` plugin
- ``openerp_proxy.ext.repr``:
  better support of ``IPython.display.HTML`` objects representation
- ``openerp_proxy.ext.sugar``:
  Added ability to access plugins directly from ``client`` instance
  For example, instead of writing ``client.plugins.Test``,
  you may write ``client.Test``
- ``stdcall`` decorator and ``stdcall``-methods.
  All methods of ``orm.object.Object`` instances,
  decorated with this decorator will be visible as
  methods of ``orm.record.Record`` and ``orm.record.RecordList``
  instances, which means that these methods could be
  called in ``meth([ids], *, context=context, **)`` format.
  All automaticaly generated proxy method are marked as ``stdcall``
  This is implemented to be able to use ``dir``-based auto-completition
  for such method for ``Record`` and ``RecordList`` instances
- ``openerp_proxy.plugin.Plugins``, ``openerp_proxy.plugin.PluginManager``,
  ``openerp_proxy.service.service.ServiceManager``,
  ``openepr_proxy.service.service.ServiceBase`` representation
  improvements (better ``__str__`` and ``__repr__`` overrides)
- Bugfix. Automaticaly clean service caches when new service class is defined
- Added ``__contains__`` override for ``module_utils`` plugin.
  Thus it is posible to check if some addon is available on odoo easier:
  ``'project_sla' in client.plugins.module_utils``
  or ``'project_sla' in client.module_utils``
- Improved documentation


Release 0.6.4
-------------

- Added ``Client.user_context`` property
- Bugfix in ``openerp_proxy.ext.repr`` with nested tables when,
  field is a function
- Fix for PR #3
- Documentation improvements

Release 0.6.3
-------------

- Added ``Record.copy()`` method override.
- HTML representation fixes and improvements

Release 0.6.2
-------------

- **experimental** Added integration with
  `AnyField <https://pypi.python.org/pypi/anyfield>`__
- Added ``RecordList.mapped`` method,
  similar to Odoo's ``RecordSet.mapped`` method.
- Partial fix related to changes in Odoo versioning.
  See `Issue #9799 <https://github.com/odoo/odoo/issues/9799>`__
- To ``module_utils`` plugin added ``update_module_list`` method.
- A bit of renaming (usualy used internaly)
  (may affect custom plugins and extensions)
  Property ``proxy``, which points to related ``Client`` instance,
  was renamed to ``client``
- Added ``tabulate`` integration. Now when app is running under IPython
  shell, it is posible to print ``RecordList``, and single ``Record``
  as normal readable tables.
  Thanks to `Tabulate <https://pypi.python.org/pypi/tabulate>`__ project
- Added ability to extend Record of specific models.
  This allows records of diferent models (objects) to behave specificaly
  This may be used for example to add virtual fields in client sripts
- Little refactored connection system. Bugs with connection via SSL (https)
  seems to be fixed. As for JSON-RPC, there are some errors may be thrown,
  telling that program cannot verify certificate. as workaround
  You may pass to Client constructor kayword argument *ssl_verify=False*
- ``log_execute_console`` Added ``TimeTracker`` context manager,
  which can be used for performance testing. It makes posible
  to get total time code was running, and how much time was spent
  on RPC requests.


Release 0.6.1
-------------

- DB service little bit refactored. added methods:
    - dump_db: wrapper around ``db.dump`` server method.
    - restore_db: wrapper around ``db.restore`` server methods.
- ``openerp_proxy.ext.repr.HField`` added ``F()`` method,
  which allows to create child field instance
- ``openerp_proxy.ext.repr`` improved styles for HTML representations


Release 0.6
-----------

- *Backward incompatible*: Changed session file format.
  *Start up imports* and *extra_paths* moved to *options* section of file.
- *Backward incompatible*: ``IPYSession`` moved to
  ``openerp_proxy.ext.repr`` extensions.
  Now when using IPython notebook, this extension have to be imported first,
  to enable HTML representation of session object.
- *Backward incompatible*: Changed signature of ``Session.connect()`` method.
- *Backward incompatible*:
  Renamed ``ERP_Proxy`` to ``Client`` and inherited objects renamed in such way
  (for example sugar extension module)
- *Backward incompatible*:
  removed ``ERP_Proxy` and ``ERP_Session`` compatability aliases
- *Backward incompatible*:
  rename ``openerp_proxy.service.service.ServiceManager.list`` to
  ``openerp_proxy.service.service.ServiceManager.service_list``.
  This affects ``Client.services`` so now ``Client.services.service_list``
  should be used instead of using ``Client.services.list``
- *Backward incompatible*:
  reports service refactored. ``wrap_result`` parametr to report
  service method removed. instead added ``generate_report`` method,
  which is recommended to use.
- Added new way reports could be generated in
  ``client.services.report[report_name].generate(report_data)``
  where ``report_data`` could be one of:

    - Record instance
    - RecordList instance
    - tuple('model.name', model_ids))

- Added HTML representation for report service objects
- Changed ``store_passwords`` option meaning. 
  now if set it will store passwords bese64 encoded,
  instead of using simple-crypt module.
  This change makes it faster to decode password,
  because last-versions of simple-crypt become too slow,
  and usualy no encryption needed here.
- Experimental *Python 3.3+* support
- Added ``HField.with_args`` method.
- Added basic implementation of graph plugin.
- Improved ``openerp_proxy.ext.log_execute_console`` extension. Added timing.
- Added ``Client.clean_caches()`` method, which is used to clean
  cache of registered models
- RecordList prefetching logic moved to cache module and highly refactored
  (Added support of prefetching of related fields)
- Added ``Client.login(dbname, user, password)`` method.
- Added ``HTMLTable.update`` method.
- Added ``RecordList.copy()`` and ``RecordList.existing()`` methods.
- Added ``HTMLTable.to_csv()`` method.
- Added ``Client.server_version`` property
- Client parametrs (dbname, user, pwd) now are not required.
  This is useful when working with ``db`` service (``client.services.db``)


Release 0.5
-----------

- Added ``RecordList.prefetch`` method. Als *RecordList's* *fields* argument
  now works.
- Changed ``Object`` class. Now it have
  ``extend_me.ExtensibleByHashType`` metaclass
  which allows it to be extended separatly for each model,
  and in general way.
  For example look at ``openerp_proxy.plugins.module_utils`` module.
- Refactored ``openerp_proxy.core`` module. + better docstrings
- ``openerp_proxy.ext.data``
    - ``RecordList.prefetch`` is disabled at the moment.
      Will be integrated in code, or atleast reimplemented in different way
    - Better ``RecordList.group_by`` method.
      Now it colud receive callable which should
      calculate key for records to group them by
    - Added ``RecordList.filter`` method.
      Useful when You want to filter records by functional field.
- Added ``openerp_proxy.ext.log_execute_console`` extension
- HTML representation for IPython notebook extension ``openerp_proxy.ext.repr``
    - Added HTML representation of
        - Record
        - Record.as_table (user is able to specify fields of record to display)
        - RecordList
        - RecordList.as_html_table (display records contained by list
          as table with abilities to highlight them by condition callables
          and to specify fields to be displayed)
        - Object.columns_info now displayed as HTML table.
    - Also *context help* in HTML representation present
- Partial context passing support in ORM
- ``openerp_proxy.orm.record`` refactored greatly
    - In this version added support of "query cache", like that one present
      in odoo's browse_record class (version 7.0).
      It is dict with data shared by records in one query.
      thus no need to read each record separatly, nor need to read all fields
      records in current query at one time.
      But major optimization which is not implemented yet is 
      implementation of some prefetching mechanism,
      to allow user to specify what fields for what model
      he would like to read, to reduce RPC calls.
    - Record class little bit optimized with slots,
      but still takes a lot of memory, because of extensibility.
    - Added ``Record.read`` method, which, performs read on record,
      store data been read to record, and returns dict with data been read
    - ``RecordList.sort`` method was added.
      implements *in-place* sort like in usual lists.
    - ``RecordList.search`` and ``RecordList.search_records``
      methods were implemented.
      The difference from standard is that these methods will automaticaly
      add [('id','in',self.ids)] to search domain
    - ``Object`` class: added properties:

        - ``model_name``: return name of object's model
        - ``model``: returns ``Record`` instance for model of this object

- Added ``module_utils`` plugin, as example and as utility to work
  with modules via RPC
- Report service wrapper (``openerp_proxy.service.report``) refactored.
    - Simplified RPC methods signatures.
    - Added wrapper on report result which can automaticaly decode and save
      report result
- Added basic options support for sessions.
  But in future this should be reimplemented as normal config
  At this moment there only one option ``store_passwords``
  which enables session to store encrypted passwords in session
  Note that encryption is very low.
  To make this option work You should install simple-crypt.
- ``ERP_Session`` renamed to ``Session`` but for backward compatability,
  there is ``ERP_Session`` name still present in module.
- Added ``IPYSession`` class.
  At this moment there is only one difference from standard ``Session`` class:
  presense of ``_repr_html_`` method.


Release 0.4
-----------

- Record objects now behaves more like browse_record in OpenERP.
  No more need in suffix '__obj' to get related fields as records.
  They will be automaticaly converted to Record objects.
- __getattribute___ in most cases changed to __getattr__
- Record._name property that returns result of name_get method for this record
- Objec.columns_info refactored to use fields_get method
  to get list of fields for an object
- Plugin system refactored. Not it is class-based.
- Added extension system, which allow to extend most of classe. For example see
  'openerp_proxy.ext' dir/package where placed some set of extensions
- All orm-related logic facored out into separate package *openerp_proxy.orm*
- session's database's aliases:
  to easily get some database in futuer, You could give it alias name
- Now it is posible to enable automatic conversion of date/time
  field value to datetime objects.
  Implemented via extension
- Sugar extension: less typing)

