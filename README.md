OpenERP proxy
=============

This project aims to ease access to openerp data via shell and used mostly for debug purposes.
This project provides interface similar to OpenERP internal code to perform operations on
OpenERP object hiding XML-RPC behind

### Features:
   * supports call to all public methods on any OpenERP object including: *read*, *search*, *write*, *unlink* and others
   * Designed not for speed but to be useful like cli client to OpenERP
   * Stores information about connection to OpenERP databases (beside passwords)
   * Provides *browse_record* like interface, allowing to browse related models too. (But doing it in defferent way than *browse_record* do
   * Use IPython as shell if it is installed, otherwise uses defaul python shell
   * Allow using separate programs (called internal *utils*) to perform some programmed logic

### What You can do with this:
   * Quickly read and analyze some data that is not visible in interface without access to DB
   * Use this project as library for code that need to access OpenERP data
   * Use in scripts that migrates OpenERP data (after, for example, adding new functionality or changing old).
     (Migration using only SQL is abd idea because of functional fields
     with *store=True* which must be recalculated.

### Alternatives:
   * [Official OpenERP client library](https://github.com/OpenERP/openerp-client-lib)

### Near future plans:
   * Add support of JSON-RPC and refactor connection system to make it extensible
     (now only XML-RPC is supported)
   * Add setup.py script


How to use
----------

Run *erp_proxy.py* file, which will open shell. If IPython is installed, then IPython shell will be opened
There in context exists *session* variable that represents current session to work with

**This project may be used as lib too. just import it and use same as below**

First connect to OpenERP database You want:

```python
>>> db = session.connect()
```

This will ask You for host, port, database, etc to connect to.
Now You have connection to OpenERP database which allows You to use database objects.

Now lets try to find how many sale orders in 'done' state we have in database:

```python
>>> sale_order_obj = db['sale.order']  # or You may use 'db.get_obj('sale.order')' if You like
>>>
>>> # Now lets search for sale orders:
>>> sale_order_obj.search([('state', '=', 'done')], count=True)
>>> 5
```

So we have 5 orders in done state. So let's read them.

Default way to read data from OpenERP is to search for required records with *search* method
which return's list of IDs of records, then read data using *read* method. Both methods
mostly same as OpenERP internal ones:

```python
>>> sale_order_ids = sale_order_obj.search([('state', '=', 'done')])
>>> sale_order_datas = sale_order_obj.read(sale_order_ids, ['name'])  # Last argument is optional.
                                                                      # it describes list of fields to read
                                                                      # if it is not provided then all fields
                                                                      # will be read
>>> sale_order_datas[0]
{'id': 3,
 'name': 'SO0004'
}
```

As we see reading data in such way allows us to get list of dictionaries where each contain fields have been read

Another way to read data is to use *search_records* or *read_records* method. Each of these methods receives
same aguments as *search* or *read* method respectively. But passing *count* argument for *search_records* will cause error.
Main difference betwen these methods in using *ERP_Record* class instead of *dict* for each record had been read.
ERP_Record class provides some orm-like abilities for records, allowing for example access fields as attributes and
provide mechanisms to lazily fetch related fields.

```python
>>> sale_orders = sale_order_obj.search_records([('state', '=', 'done')])
>>> sale_orders[0]
... ERP_Record of ERP Object ('sale.order'),9
>>>
>>> # So we have list of ERP_Record objects. Let's check what they are
>>> so = sale_orders[0]
>>> so.id
... 9
>>> so.name
... SO0011
>>> so.partner_id  # many2one field values are consists of ID of related record and name of related record
... [25, 'Better Corp']
>>>
>>> # Lets fetch related partner obj. To do it just add suffix '__obj' to and of field name
>>> so.partner_id__obj
... ERP_Record of ERP Object ('res.partner'),25
>>> so.partner_id__obj.name
... Better Corp
>>> so.partner_id__obj.active
... True
```

For more information see source code.
