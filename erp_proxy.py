#!/usr/bin/env python
# -*- coding: utf8 -*-

# TODO: Make it as simple [for usage] as it could be

""" This module provides some classes to simplify acces to OpenERP server via xmlrpc.
    Some of these classes are may be not safe enough and should be used with carefully

    Example ussage of this module:

    >>> erp_db = ERP_Proxy('dbname', 'server.com', 'some_user', 'mypassword')
    >>> sale_obj = erp_db['sale_order']
    >>> sale_ids = sale_obj.search([('state','not in',['done','cancel'])])
    >>> sale_data = sale_obj.read(sale_ids, ['name'])
    >>> for order in sale_data:
    ...     print "%5s :    %s" % (order['id'],order['name'])
    >>> tmpl_ids = erp_db['product.template'].search([('name','ilike','template_name')])
    >>> print erp_db['product.product'].search([('product_tmpl_id','in',tmpl_ids)])

    >>> db = ERP_Proxy(dbname='jbm0', 'erp.jbm.int', 'your_user')
    >>> so = db['sale.order']
    >>> order_ids = so.search([('state','=','done')])
    >>> order = so.read(order_ids[0])

    Also You can call any method (beside private ones starting with underscore(_)) of any model.
    For example to check availability of stock move all You need is:
    >>> db = session.connect()
    >>> move_obj = db['stock.move']
    >>> move_ids = [1234] # IDs of stock moves to be checked
    >>> move_obj.check_assign(move_ids)
"""

import xmlrpclib
from getpass import getpass
import functools
import json
import os.path
import pprint
import imp

# project imports
from utils import AttrDict
from utils import ustr


class ERPProxyException(Exception):
    pass


class ERP_Proxy(object):
    """ A simple class to connect ot ERP via xml_rpc
        Should be initialized with following arguments:
            ERP_Proxy(dbname, host, user, pwd = getpass('Password: '), verbose = False)

        Allows access to ERP objects via dictionary syntax:
            >>> db = ERP_Proxy(...)
            >>> db['sale.order']
                ERP_Object: 'sale.order'

        TODO: describe methods and how to use them

    """

    def __init__(self, dbname, host, user, pwd=None, port=8069, verbose=False):
        self.dbname = dbname
        self.host = host
        self.user = user
        self.port = port
        self.pwd = pwd or getpass('Password: ')
        self.verbose = verbose

        self.__objects = {}   # cached objects

        # properties
        self.__last_result = None
        self.__last_result_wkf = None
        self.__registered_objects = None

        self.__use_execute_kw = True

        self.uid = None
        self.__services = {}

        # Connect to database
        self.connect()

    def use_execute_kw(self, val=True):
        """ Controlls what execute method version to use by default.
            Default is True which means to use execute_kw
            But for version 6 databases execute_kw method is not defined, so
            befor using database this method should be called with value False:
                >>> db.use_execute_kw(False)
        """
        self.__use_execute_kw = val

    @property
    def registered_objects(self):
        """ Stores list of registered in ERP database objects
        """
        if self.__registered_objects is not None:
            return self.__registered_objects
        t1, t2 = self.__last_result, self.__last_result_wkf
        ids = self.execute('ir.model', 'search', [])
        read = self.execute('ir.model', 'read', ids, ['model'])
        self.__registered_objects = [x['model'] for x in read]
        self.__last_result, self.__last_result_wkf = t1, t2
        return self.__registered_objects

    @property
    def last_result(self):
        """ Stores last value returned by 'execute' method
        """
        return self.__last_result

    @property
    def last_result_wkf(self):
        """ Stores last value returned by 'execute_wkf' method
        """
        return self.__last_result_wkf

    def get_service(self, name):
        if name in self.__services:
            return self.__services[name]

        service = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/%s' % (self.host, self.port, name), verbose=self.verbose)
        self.__services[name] = service
        return service

    def connect(self):
        """ Connects to the server

            returns Id of user connected
        """
        # Get the uid
        service_auth = self.get_service('common')
        self.uid = service_auth.login(self.dbname, self.user, self.pwd)

        if not self.uid:
            raise ERPProxyException("Bad login or password")

        return self.uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches
        """
        self.connect()

        self.__last_result = None
        self.__last_result_wkf = None

    # Report related methods
    def report(self, report_name, ids, context):
        """ Proxy to report service *report* method

            @param report_name: string representing name of report service
            @param ids: list of object ID to get report for
            @param context: Ususaly have to have 'model' and 'id' keys that describes object to get report for
            @return: ID of report to get by method *report_get*
        """
        return self.get_service('report').report(self.dbname, self.uid, self.pwd, report_name, ids, context)

    def report_get(self, report_id):
        """ Proxy method to report servce *report_get* method

            @param report_id: int that represents ID of report to get
            @return: dictinary with keys:
                         'state': boolean, True if report generated correctly
                         'result': base64 encoded content of report
                         'format': string representing format, report generated in

        """
        return self.get_service('report').report_get(self.dbname, self.uid, self.pwd, report_id)

    # Object related methods
    def execute(self, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        self.__last_result = self.get_service('object').execute(self.dbname, self.uid, self.pwd, *args, **kwargs)
        return self.__last_result

    def execute_kw(self, obj, method, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        self.__last_result = self.get_service('object').execute_kw(self.dbname, self.uid, self.pwd, obj, method, args, kwargs)
        return self.__last_result

    def execute_default(self, *args, **kwargs):
        if self.__use_execute_kw:
            return self.execute_kw(*args, **kwargs)
        return self.execute(*args, **kwargs)

    def execute_wkf(self, *args, **kwargs):
        """First arguments should be 'object' and 'signal' and 'id'
        """
        self.__last_result_wkf = self.get_service('object').exec_workflow(self.dbname, self.uid, self.pwd, *args, **kwargs)
        return self.__last_result_wkf

    def get_obj(self, object_name):
        """ Returns wraper around openERP object 'object_name' which is instance of ERP_Object

            @param object_name: name of an object to get wraper for
            @return: instance of ERP_Object which wraps choosen object
        """
        if object_name in self.__objects:
            return self.__objects[object_name]

        if object_name not in self.registered_objects:
            raise ValueError("There is no object named '%s' in ERP" % object_name)

        obj = ERP_Object(self, object_name)
        self.__objects[object_name] = obj
        return obj

    def __getitem__(self, name):
        """ Returns instance of ERP_Object with name 'name'
        """
        res = None
        try:
            res = self.get_obj(name)
        except ValueError:
            raise KeyError('Wrong object name')

        return res

    def get_url(self):
        return "%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=self.user,
                                                                host=self.host,
                                                                database=self.dbname,
                                                                port=self.port)

    def __str__(self):
        return "ERP_Proxy object: %s" % self.get_url()
    __repr__ = __str__


def MethodWrapper(erp_proxy, object_name, method_name):
    """ Wraper around ERP objects's methods.

        for internal use.
        It is used in ERP_Object class.
    """
    def wrapper(*args, **kwargs):
        try:
            res = erp_proxy.execute_default(object_name, method_name, *args, **kwargs)
        except xmlrpclib.Fault as exc:
            raise ERPProxyException(u"A fault occured\n"
                                    u"Fault code: %s\n"
                                    u"Fault string: %s\n"
                                    u"" % (ustr(exc.faultCode),
                                           ustr(exc.faultString)))
        return res
    return wrapper


class ERP_Record(AttrDict):
    """ A simple class to wrap OpenERP records

        All fields could be used as dictionary items and as attributes of object
        All methods could be accessed as attibutes of class, and they will be automaticaly
        proxied to related ERP_Object instance passing as IDs [self.id]

        Special methods:
            - refresh() - rereads data for this object
    """

    # TODO: think about optimization via slots
    # TODO: add more doc on aditional functionality like using __obj suffix to
    # access related by many2one records

    def __init__(self, obj, data):
        assert isinstance(obj, ERP_Object), "obj should be ERP_Object"
        assert isinstance(data, dict), "data should be dictionary structure returned by ERP_Object.read"
        self.__obj = obj
        self.__related_objects = {}
        self.__related_objects_o2m = {}
        self.__workflow_instance = None
        self.update(data)

    def __dir__(self):
        res = dir(super(ERP_Record, self))
        res.extend(self.keys())
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    def _get_obj(self):
        """ Returns instance of related ERP_Object
        """
        return self.__obj

    def _get_proxy(self):
        """ Returns instance of related ERP_Proxy object
        """
        return self.__obj._get_proxy()

    def _get_columns_info(self):
        """ Returns dictionary with information about columns of related object
        """
        return self.__obj._get_columns_info()

    def _get_workflow_instance(self):
        """ Retunrs workflow instance related to this record
        """
        if self.__workflow_instance is None:
            wkf = self.__obj._get_workflow()
            if not wkf:
                self.__workflow_instance = False
            else:
                wkf_inst_obj = self._get_proxy().get_obj('workflow.instance')
                wkf_inst_records = wkf_inst_obj.search_records([('wkf_id', '=', wkf.id),
                                                                ('res_id', '=', self.id)], limit=1)
                self.__workflow_instance = wkf_inst_records and wkf_inst_records[0] or False
        return self.__workflow_instance

    def _get_workflow_items(self):
        """ Returns list of related workflow.woritem objects
        """
        # TODO: think about adding caching
        workitem_obj = self._get_proxy().get_obj('workflow.workitem')
        wkf_inst = self._get_workflow_instance()
        if wkf_inst:
            return workitem_obj.search_records([('inst_id', '=', wkf_inst.id)])
        return []

    def __str__(self):
        return "ERP_Record of %s,%s" % (self.__obj, self.id)
    __repr__ = __str__

    def __getattribute__(self, name):
        res = None
        try:
            res = super(ERP_Record, self).__getattribute__(name)
        except AttributeError:
            try:
                res = self[name]
            except KeyError:
                method = getattr(self.__obj, name)
                res = functools.partial(method, [self.id])
        return res

    def __get_many2one_rel_obj(self, name, cached=True):
        """ Method used to fetch related object by name of field that points to it
        """
        if name not in self.__related_objects or not cached:
            relation = self._get_columns_info()[name].relation
            rel_obj = self._get_proxy().get_obj(relation)
            rel_id = self[name][0]   # Do not forged about relations in form [id, name]
            self.__related_objects[name] = rel_obj.read_records(rel_id)
        return self.__related_objects[name]

    def __get_one2many_rel_obj(self, name, cached=True, limit=None):
        """ Method used to fetch related objects by name of field that points to them
            using one2many relation
        """
        if name not in self.__related_objects_o2m or not cached:
            relation = self._get_columns_info()[name].relation
            rel_obj = self._get_proxy().get_obj(relation)
            rel_ids = self[name]   # Take in mind that field value is list of IDS
            self.__related_objects_o2m[name] = rel_obj.read_records(rel_ids)
        return self.__related_objects_o2m[name]

    def __getitem__(self, name):
        res = None
        try:
            res = super(ERP_Record, self).__getitem__(name)
        except KeyError:
            # Allow using '__obj' suffix in field name to retryve ERP_Record
            # instance of object related via many2one or one2many
            # This means next:
            #    >>> o = db['sale.order.line'].read_records(1)
            #    >>> o.order_id
            #    ... [25, 'order_name']
            #    >>> o.order_id__obj
            #    ... ERP_Record of sale.order, 25
            if name.endswith('__obj'):
                fname = name[:-5]
                col_info = self._get_columns_info()[fname]
                if col_info.ttype == 'many2one':
                    res = self.__get_many2one_rel_obj(fname)
                elif col_info.ttype == 'one2many' or col_info.ttype == 'many2many':
                    res = self.__get_one2many_rel_obj(fname)
                else:
                    raise
            else:
                raise

        return res

    def refresh(self):
        self.update(self.__obj.read(self.id))

        # Update related objects cache
        self.__related_objects = {}
        self.__related_objects_o2m = {}

    def workflow_trg(self, signal):
        """ trigger's specified signal on record's related workflow
        """
        return self._get_obj().workflow_trg(self.id, signal)


class ERP_Object(object):
    """ A simple class to simplify operations on ERP objects.
        It gives interface like open ERP osv.osv objects.

        Example:
        >>> erp = ERP_Proxy(...)
        >>> sale_obj = ERP_Object(erp, 'sale.order')
        >>> sale_obj.search([('state','not in',['done','cancel'])])

        Special methods:
            - search_records - receives same arguments as 'search' method,
                               but returns list of ERP_Record objects or False
            - read_records - receives same arguments as 'read', but returns
                             list of ERP_Record objects. Or if single int passed as IDs
                             it will returns single ERP_Record object
    """

    # TODO: add doc on new methods ?
    def __init__(self, erp_proxy, object_name):
        self.__erp_proxy = erp_proxy
        self.__obj_name = object_name
        self.__columns_info = None
        self.__workflow = None

    def _get_proxy(self):
        return self.__erp_proxy

    def __dir__(self):
        res = dir(super(ERP_Object, self))
        res.extend(['read', 'search', 'write', 'unlink', 'create'])
        return res

    def _get_columns_info(self):
        """ Reads information about fields available on model
        """
        if self.__columns_info is None:
            columns_info = {}
            fields_obj = self.__erp_proxy['ir.model.fields']
            fields = fields_obj.search_records([('model', '=', self.__obj_name)])
            for field in fields:
                columns_info[field.name] = field

            self.__columns_info = columns_info

        return self.__columns_info

    def _get_workflow(self):
        """ Returns ERP_Record instance of "workflow" object
            related to this ERP_Object

            If there are no workflow for an object then False will be returned
        """
        if self.__workflow is None:
            wkf_obj = self.__erp_proxy['workflow']
            # TODO: implement correct behavior for situations with few
            # workflows for same model.
            wkf_records = wkf_obj.search_records([('osv', '=', self.__obj_name)])
            if wkf_records and len(wkf_records) > 1:
                raise ERPProxyException("More then one workflow per model not supported "
                                        "be current version of openerp_proxy!")
            self.__workflow = wkf_records and wkf_records[0] or False
        return self.__workflow

    def search_records(self, *args, **kwargs):
        """ Return instance or list of instances of ERP_Record class,
            making available to work with data simpler:
                >>> so_obj = db['sale.order']
                >>> data = so_obj.search_records([('date','>=','2013-01-01')])
                >>> for order in data:
                        order.write({'note': 'order date is %s'%order.date})
        """

        res = self.search(*args, **kwargs)
        if not res:
            return False
        if isinstance(res, (int, long)):
            return ERP_Record(self, self.read(res))
        if isinstance(res, (list, tuple)):
            return [ERP_Record(self, data) for data in self.read(res)]

    def read_records(self, ids, *args, **kwargs):
        """ Return instance or list of instances of ERP_Record class,
            making available to work with data simpler:
                >>> so_obj = db['sale.order']
                >>> data = so_obj.search_records([('date','>=','2013-01-01')])
                >>> for order in data:
                        order.write({'note': 'order data is %s'%order.data})
        """
        assert isinstance(ids, (int, long, list, tuple)), "ids must be instance of (int, long, list, tuple)"
        if isinstance(ids, (int, long)):
            return ERP_Record(self, self.read(ids, *args, **kwargs))
        if isinstance(ids, (list, tuple)):
            return [ERP_Record(self, data) for data in self.read(ids, *args, **kwargs)]

    def workflow_trg(self, obj_id, signal):
        """ Triggers specified signal for object's workflow
        """
        assert isinstance(obj_id, (int, long)), "obj_id must be integer"
        assert isinstance(signal, basestring), "signal must be string"
        return self._get_proxy().execute_wkf(self.__obj_name, signal, obj_id)

    def __getattribute__(self, name):
        res = None
        try:
            res = super(ERP_Object, self).__getattribute__(name)
        except AttributeError:
            res = MethodWrapper(self.__erp_proxy, self.__obj_name, name)

        return res

    def __str__(self):
        return "ERP Object ('%s')" % self.__obj_name
    __repr__ = __str__


def connect(dbname=None, host=None, user=None, pwd=None, port=8069, verbose=False):
    """ Wraper aroun ERP_Proxy constructor class to simplify connect from shell.

        @param dbname: name of database to connect to (will be asked interactvely if not provided)
        @param host: host name to connect to (will be asked interactvely if not provided)
        @param user: user name to connect as (will be asked interactvely if not provided)
        @param pwd: password for selected user (will be asked interactvely if not provided)
        @param port: port to connect to. (default: 8069)
        @param verbose: to be verbose, or not to be. (default: False)
        @return: ERP_Proxy object
    """
    host = host or raw_input('Server Host: ')
    dbname = dbname or raw_input('Database name: ')
    user = user or raw_input('ERP Login: ')
    pwd = pwd or getpass('Password: ')
    return ERP_Proxy(dbname=dbname, host=host, user=user, pwd=pwd, port=port, verbose=verbose)


class UtilInitError(Exception):
    pass


class ERP_Utils(object):
    def __init__(self, erp_proxy, util_classes):
        """ @param erp_proxy: ERP_Proxy object to bind utils set to
            @param util_classes: dict with {util_name: util_class}

            # NOTE: util classes should be a reference to dict saved in session
            # for example. this allows this dict to be updated from session and
            # all changes from session will be reflected here allowing to add
            # new utils dynamically.
        """
        self.__erp_proxy = erp_proxy
        self.__util_classes = util_classes
        self.__utils = {}

    def __getitem__(self, name):
        util = self.__utils.get(name, False)
        if util is False:
            util_cls = self.__util_classes[name]
            try:
                util = util_cls(self.__erp_proxy)
            except Exception as exc:
                raise UtilInitError(exc)
            self.__utils[name] = util
        return util

    def __getattribute__(self, name):
        try:
            return super(ERP_Utils, self).__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    def __dir__(self):
        return self.__util_classes.keys()


class ERP_Session(object):

    """ Simple session manager which allows to manage databases easier
        This class stores information about databases You used in home
        directory, and on init it loads history and allows simply connect
        to database by url or index. No more hosts, usernames, ports, etc...
        required to be memorized.
        Just on session start call:
            print session
        And You will get all databases You worked with listed as (index, url) pairs.
        to connect to one of thouse databases just call session[index|url] and required
        ERP_Proxy object will be returned.
    """

    def __init__(self, data_file='~/.erp_proxy.json'):
        self.data_file = os.path.expanduser(data_file)
        self._databases = {}  # key: url; value: instance of DB or dict with init args

        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as json_data:
                self._databases = json.load(json_data)

        self._db_index = {}  # key: index; value: url
        self._db_index_rev = {}  # key: url; value: index
        self._db_index_counter = 0

        self._util_classes = {}

    def add_util(self, cls):
        self._util_classes[cls._name] = cls

    def load_util(self, path):
        """ Loads utils from specified path, which should be a python module
            or python package (not tested yet) which defines function
            'erp_proxy_plugin_init' which should return dictionary with
            key 'utils' which points to list of utility classes. each class must have
            class level attribute _name which will be used to access it from session
            or db objects. So as masic example util module may look like:

                class MyUtil(object):
                    _name = 'my_util'

                    def __init__(self, db):  # db is required argument passed by infrastructure
                        self.db = db

                    ...

                def erp_proxy_plugin_init():
                    return {'utils': [MyUtil]}
        """
        # TODO: Add ability to save utils files used in conf.
        name = os.path.splitext(os.path.basename(path))[0]
        module_name = 'erp_proxy.%s' % name
        module = imp.load_source(module_name, path)
        plugin_data = module.erp_proxy_plugin_init()
        for cls in plugin_data.get('utils', []):
            self.add_util(cls)

    @property
    def index(self):
        """ Property which returns dict with {index: url}
        """
        if not self._db_index:
            for url in self._databases.keys():
                self._index_url(url)
        return dict(self._db_index)

    def _index_url(self, url):
        """ Returns index of specified URL, or adds it to
            store assigning new index
        """
        if self._db_index_rev.get(url, False):
            return self._db_index_rev[url]

        self._db_index_counter += 1
        self._db_index[self._db_index_counter] = url
        self._db_index_rev[url] = self._db_index_counter
        return self._db_index_counter

    def _add_db(self, url, db):
        """ Add database to history
        """
        self._databases[url] = db
        self._index_url(url)

    def get_db(self, url_or_index):
        if isinstance(url_or_index, (int, long)):
            url = self._db_index[url_or_index]
        else:
            url = url_or_index

        db = self._databases.get(url, False)
        if not db:
            raise ValueError("Bad url %s. not found in history nor databases" % url)

        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(**db)
        # injecting utils:
        db.utils = ERP_Utils(db, self._util_classes)
        # utils injected
        self._add_db(url, db)
        return db

    @property
    def db_list(self):
        return self._databases.keys()

    def connect(self, dbname=None, host=None, user=None, pwd=None, port=8069, verbose=False):
        """ Wraper aroun ERP_Proxy constructor class to simplify connect from shell.

            @param dbname: name of database to connect to (will be asked interactvely if not provided)
            @param host: host name to connect to (will be asked interactvely if not provided)
            @param user: user name to connect as (will be asked interactvely if not provided)
            @param pwd: password for selected user (will be asked interactvely if not provided)
            @param port: port to connect to. (default: 8069)
            @param verbose: to be verbose, or not to be. (default: False)
            @return: ERP_Proxy object
        """
        host = host or raw_input('Server Host: ')
        dbname = dbname or raw_input('Database name: ')
        user = user or raw_input('ERP Login: ')

        url = "%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=user,
                                                               host=host,
                                                               database=dbname,
                                                               port=port)
        db = self._databases.get(url, False)
        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(dbname=dbname, host=host, user=user, pwd=pwd, port=port, verbose=verbose)
        self._add_db(url, db)
        return db

    def save(self):
        data = {}
        for url, database in self._databases.iteritems():
            if isinstance(database, ERP_Proxy):
                init_args = {
                    'dbname': database.dbname,
                    'host': database.host,
                    'port': database.port,
                    'user': database.user,
                    'verbose': database.verbose,
                }
            else:
                init_args = database
            assert isinstance(init_args, dict), "init_args must be instance of dict"
            data[url] = init_args

        with open(self.data_file, 'wt') as json_data:
            json.dump(data, json_data)

    def __getitem__(self, url_or_index):
        return self.get_db(url_or_index)

    def __str__(self):
        return pprint.pformat(self.index)

    def __repr__(self):
        return pprint.pformat(self.index)


def main():
    """ Entry point for running as standalone APP
    """
    session = ERP_Session()

    header_databases = "\n"
    for index, url in session.index.iteritems():
        header_databases += "        - [%s] %s\n" % (index, url)

    header = """
    Usage:
        >>> db = session.connect()
        >>> so_obj = db['sale.orderl']  # get object
        >>> dir(so_obj)  # Thid will show all default methods of object
        >>> so_id = 123 # ID of sale order
        >>> so_obj.read(so_id)
        >>> so_obj.write([so_id], {'note': 'Test'})
        >>> sm_obj = db['stock.move']
        >>>
        >>> # check availability of stock move
        >>> sm_obj.check_assign([move_id1, move_id2,...])

    Available objects in context:
        ERP_Proxy - class that represents single OpenERP database and
                    provides methods to work with data. Instances of this
                    class returned by connect() method of session object.
        session - represents session of client, stores in home directory list
                  of databases user works with, to simplify work. It is simpler
                  to get list of databases you have worked with previously on program
                  start, and to connect to them without remembrering hosts, users, ports
                  and other unneccesary information

    Databases You previously worked with: %(databases)s

        (Used index or url for session: session[1] or session[url])
    """ % {'databases': header_databases}

    _locals = {
        'ERP_Proxy': ERP_Proxy,
        'session': session,
    }
    try:
        from IPython import embed
        embed(user_ns=_locals, header=header)
    except ImportError:
        from code import interact
        interact(local=_locals, banner=header)

    session.save()

if __name__ == '__main__':
    main()
