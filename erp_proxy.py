#!/usr/bin/env python
# -*- coding: utf8 -*-

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



# TODO : add report interface
# TODO : add ability to create configurations in home directory
class ERPProxyException(Exception):
    pass


class AttrDict(dict):
    """ Simple class to make dictionary able to use attribute get operation
        to get elements it contains using syntax like:

        >>> d = AttrDict(arg1=1, arg2='hello')
        >>> print d.arg1
            1
        >>> print d.arg2
            hello
        >>> print d['arg2']
            hello
        >>> print d['arg1']
            1
    """
    def __getattribute__(self, name):
        try:
            return super(AttrDict, self).__getattribute__(name)
        except AttributeError:
            try:
                return super(AttrDict, self).__getitem__(name)
            except KeyError:
                raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class ERP_Proxy(object):
    """ A simple class to connect ot ERP via xml_rpc
        Should be initialized with following arguments:
            ERP_Proxy(dbname, host, user, pwd = getpass('Password: '), verbose = False)

        Allows access to ERP objects via dictionary syntax:
            >>> db = ERP_Proxy(...)
            >>> db['sale.order']
                ERP_Object: 'sale.order'


    """

    def __init__(self, dbname, host, user, pwd=None, port=8069, verbose=False):
        self.dbname = dbname
        self.host = host
        self.user = user
        self.port = port
        self.pwd = pwd or getpass('Password: ')
        self.verbose = verbose

        self.connect()
        self.__objects = {}   # cached objects

        # properties
        self.__last_result = None
        self.__last_result_wkf = None
        self.__registered_objects = None

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

    def connect(self):
        """ Connects to the server

            returns Id of user connected
        """
        # Get the uid
        self.sock_common = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (self.host, self.port), verbose=self.verbose)
        self.uid = self.sock_common.login(self.dbname, self.user, self.pwd)
        self.sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (self.host, self.port), verbose=self.verbose)
        return self.uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches
        """
        self.connect()

        self.__last_result = None
        self.__last_result_wkf = None

    def execute(self, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        self.__last_result = self.sock.execute(self.dbname, self.uid, self.pwd, *args, **kwargs)
        return self.__last_result

    def execute_wkf(self, *args, **kwargs):
        """First arguments should be 'object' and 'signal' and 'id'
        """
        self.__last_result_wkf = self.sock.exec_workflow(self.dbname, self.uid, self.pwd, *args, **kwargs)
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
        try:
            return self.get_obj(name)
        except ValueError:
            raise KeyError('Wrong object name')

    def get_url(self):
        return "%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=self.user,
                                                                host=self.host,
                                                                database=self.dbname,
                                                                port=self.port)

    def __str__(self):
        return "ERP_Proxy object: %s" % self.get_url()
    __repr__ = __str__


class MethodWraper(object):
    """ Wraper class around ERP objcts's methods.
        it is callable and shoud bechave like simple function

        This class is for internal use.
        It is used in ERP_Object class.
    """
    def __init__(self, erp_proxy, object_name, method_name):
        self.__erp_proxy = erp_proxy
        self.__obj_name = object_name
        self.__name = method_name

    def __call__(self, *args, **kwargs):
        try:
            res = self.__erp_proxy.execute(self.__obj_name, self.__name, *args, **kwargs)
        except xmlrpclib.Fault as exc:
            raise ERPProxyException("A fault occured\n"
                                    "Fault code: %s\n"
                                    "Fault string: %s\n"
                                    "" % (exc.faultCode,
                                          exc.faultString))
        return res

    def __str__(self):
        return "ERP Objects Method: ('%s').%s" % (self.__obj_name, self.__name)
    __repr__ = __str__


class ERP_Record(AttrDict):
    """ A simple class to wrap OpenERP records
        For internal use only.
    """

    def __init__(self, obj, data):
        assert isinstance(obj, ERP_Object), "obj should be ERP_Object"
        assert isinstance(data, dict), "data should be dictionary structure returned by ERP_Object.read"
        self.__obj = obj
        self.update(data)

    def __str__(self):
        return "ERP_Record of %s,%s" % (self.__obj, self.id)
    __repr__ = __str__

    def __getattribute__(self, name):
        try:
            return super(ERP_Record, self).__getattribute__(name)
        except AttributeError:
            method = getattr(self.__obj, name)
            return functools.partial(method, [self.id])

    def refresh(self):
        self.update(self.__obj.read(self.id))


class ERP_Object(object):
    """ A simple class to simplify operations on ERP objects.
        It gives interface like open ERP osv.osv objects.

        Example:
        >>> erp = ERP_Proxy(...)
        >>> sale_obj = ERP_Object(erp, 'sale.order')
        >>> sale_obj.search([('state','not in',['done','cancel'])])
    """

    def __init__(self, erp_proxy, object_name):
        self.__erp_proxy = erp_proxy
        self.__obj_name = object_name

    def __dir__(self):
        return ['search_records', 'read_records', 'read', 'search', 'write', 'unlink', 'create']

    def search_records(self, *args, **kwargs):
        """ Return instance or list of instances of ERP_Record class,
            making available to work with data simpler:
                >>> so_obj = db['sale.order']
                >>> data = so_obj.search_records([('date','>=','2013-01-01')])
                >>> for order in data:
                        order.write({'note': 'order data is %s'%order.data})
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

    def __getattribute__(self, name):
        try:
            return super(ERP_Object, self).__getattribute__(name)
        except AttributeError:
            return MethodWraper(self.__erp_proxy, self.__obj_name, name)

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


class ERP_Session(object):

    """ Simple session manager which allows to manager databases You worjing with easier
    """

    def __init__(self, data_file='~/.erp_proxy.json'):
        self.data_file = os.path.expanduser(data_file)
        self._databases = {}  # key: url; value: instance of DB or dict with init args

        if os.path.exists(self.data_file):
            with open(self.data_file, 'rt') as json_data:
                self._databases = json.load(json_data)

    def get_db(self, url):
        db = self._databases.get(url, False)
        if not db:
            raise ValueError("Bad url %s. not found in history nor databases" % url)

        if isinstance(db, ERP_Proxy):
            return db

        db = ERP_Proxy(**db)
        self._databases[url] = db
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
        self._databases[url] = db
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

    def __getitem__(self, url):
        return self.get_db(url)

if __name__ == '__main__':

    session = ERP_Session()

    header_databases = "\n        - ".join(session.db_list)

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

    Databases You previously worked with:
        - %(databases)s
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
