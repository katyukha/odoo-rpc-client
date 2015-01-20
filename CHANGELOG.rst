Master:
    - Changed ``Object`` class. Now it have ``extend_me.ExtensibleByHashType`` metaclass
      which allows it to be extended separatly for each model, and in general way.
      For example of extending for specific model look at ``openerp_proxy.plugins.module_utils``
      module.
    - Refactored ``openerp_proxy.core`` module. + better docstrings
    - ``openerp_proxy.ext.data``
        - ``RecordList.prefetch`` is disabled at the moment. Will be integrated in code, or atleast
          reimplemented in different way
        - Better ``RecordList.group_by`` method. Now it colud receive callable which should
          calculate key for records to group them by
        - Added ``RecordList.filter`` method. Useful when You want to filter records by functional field.
    - Added ``openerp_proxy.ext.log_execute_console`` extension
    - HTML representation for IPython notebook extension ``openerp_proxy.ext.repr``
        - Added HTML representation of
            - Record
            - Record.as_table (user is able to specify fields of record to display)
            - RecordList
            - RecordList.as_html_table (display records conteined by list as table with
              abilities to highlight them by condition collable and to specify fields to be displayed)
            - Object.columns_info now displayed as HTML table.
        - Also *context help* in HTML representation present
    - Partial context passing support in ORM
    - ``openerp_proxy.orm.record`` refactored greatly
        - In this version added support of "query cache" like that one is present
          in odoo's browse_record class (version 7.0). So there are dict with data shared
          by records in one query. thus no need to read each record separatly, nor need to read all fields
          and for all records at once. This allows to read only those fields that are asked and for all
          records in current query at one time. But major optimization which is not implemented yet is 
          implementation of some prefetching mechanism, to allow user to specify what fields for what model
          he would like to read, to reduce RPC calls.
        - Record class little bit optimized with slots, but still takes a lot of memory, because of extensibility.
        - Added ``Record.read`` method, which, performs read on record, store data been read to record, and
          returns data dictionary been read
        - ``RecordList.sort`` method was added. implements *in-place* sort like in usual lists.
        - ``RecordList.search`` and ``RecordList.search_records`` methods were implemented.
          The difference from standard is that these methods will automaticaly add [('id','in',self.ids)] to
          search domain
        - To ``Object`` class added properties ``model_name`` (which return name fields obj object's model)
          and ``model`` which returns ``Record`` instance for model of this object
    - Added ``module_utils`` plugin, as example and as utility to work with modules via RPC
    - Report service wrapper (``openerp_proxy.service.report``) refactored. simplified RPC methods signatures.
      And added wrapper on report result which can automaticaly decode and save report result
    - Added basic options support for sessions. But in future this should be reimplemented as normal config
      At this moment there only one option ``store_passwords`` which enables session to store encrypted passwords in session
      Note that encryption is very low. To make this option work You should install simple-crypt.
    - ``ERP_Session`` renamed to ``Session`` but for backward compatability there still ``ERP_Session`` name is present in module.
    - Added ``IPYSession`` class. At this moment only difference from standard is presense of ``_repr_html_`` method.

Version 0.4
    - Record objects now behaves more like browse_record in OpenERP.
      No more need in suffix '__obj' to get related fields as records.
      They will be automaticaly converted to Record objects.
    - __getattribute___ in most cases changed to __getattr__
    - Record._name property that returns result of name_get method for this record
    - Objec.columns_info refactored to use fields_get method to get list of fields for an object
    - Plugin system refactored. Not it is class-based.
    - Added extension system, which allow to extend most of classe. For example see
      'openerp_proxy.ext' dir/package where placed some set of extensions
    - All orm-related logic facored out into separate package *openerp_proxy.orm*
    - session's database's aliases. to easily get some database in futuer, You could give it alias name
    - Not it is posible to enable automatic conversion of date/time field value to datetime objects.
      Implemented via extension
    - Sugar extension: less typing)

