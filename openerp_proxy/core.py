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

    >>> db = ERP_Proxy(dbname='db0', 'erp.host.com', 'your_user')
    >>> so = db['sale.order']
    >>> order_ids = so.search([('state','=','done')])
    >>> order = so.read(order_ids[0])

    Also You can call any method (beside private ones starting with underscore(_)) of any model.
    For example to check availability of stock move all You need is:

    >>> db = session.connect()
    >>> move_obj = db['stock.move']
    >>> move_ids = [1234] # IDs of stock moves to be checked
    >>> move_obj.check_assign(move_ids)

    Ability to use Record class as analog to browse_record:

    >>> move_obj = db['stock.move']
    >>> move = move_obj.browse(1234)
    >>> move.state
    ... 'confirmed'
    >>> move.check_assign()
    >>> move.refresh()
    >>> move.state
    ... 'assigned'
    >>> move.picking_id
    ... R('stock.picking', 12)['OUT-12']
    >>> move.picking_id.id
    ... 12
    >>> move.picking_id.name
    ... 'OUT-12'
    >>> move.picking_id_.state
    ... 'assigned'
"""


# project imports
from openerp_proxy.connection import get_connector
from openerp_proxy.exceptions import Error
from openerp_proxy.service import ServiceManager
from openerp_proxy.plugin import PluginManager

# Activate orm internal logic
# TODO: think about not enabling it by default, allowing users to choose what
# thay woudld like to use. Or simply create two entry points (one with all
# enabled by default and another with only basic stuff which may be useful for
# libraries that would like to get speed instead of better usability
import openerp_proxy.orm

from extend_me import Extensible


__all__ = ('ERPProxyException', 'ERP_Proxy')


class ERPProxyException(Error):
    pass


class ERP_Proxy(Extensible):
    """
       A simple class to connect ot ERP via xml_rpc
       Should be initialized with following arguments:

       :param str dbname: name of database to connect to
       :param str host: server host name to connect to
       :param str user: username to login as
       :param str pwd: password to log-in with
       :param int port: port number of server
       :param str protocol: protocol used to connect. To get list of available protcols call:
                            ``openerp_proxy.connection.get_connector_names()``
       :param bool verbose: Be verbose?

       Example::

           >>> db = ERP_Proxy('dbname', 'host', 'user', pwd = 'Password', verbose = False)

       Allows access to ERP objects via dictionary syntax::

           >>> db['sale.order']
               Object ('sale.order')
    """

    def __init__(self, dbname, host, user, pwd, port=8069, protocol='xml-rpc', verbose=False):
        self._dbname = dbname
        self._username = user
        self._pwd = pwd

        self._connection = get_connector(protocol)(host, port, verbose=verbose)
        self._services = ServiceManager(self)
        self._plugins = PluginManager(self)

        self._uid = None
        self._user = None

    @property
    def dbname(self):
        """ Name of database to connect to
        """
        return self._dbname

    @property
    def username(self):
        """ Name of user to connect with (user login)
        """
        return self._username

    @property
    def host(self):
        """ Server host
        """
        return self._connection.host

    @property
    def port(self):
        """ Server port
        """
        return self._connection.port

    @property
    def protocol(self):
        """ Server protocol
        """
        return self._connection.Meta.name

    @property
    def services(self):
        """ ServiceManager instance, which contains list
            of all available services for current connection,
            accessible by name::

                db.services.report   # report service
                db.services.object   # object service (model related actions)
                db.services.common   # used for login (db.services.common.login(dbname, username, password)
                db.services.db       # database management service

        """
        return self._services

    @property
    def plugins(self):
        """ Plugins associated with this proxy instance
        """
        return self._plugins

    @property
    def connection(self):
        """ Connection to server.
        """
        return self._connection

    @property
    def uid(self):
        """ Returns ID of current user. if one is None,
            connects to database and returns it

            :rtype: int
        """
        if self._uid is None:
            self._uid = self.connect()
        return self._uid

    @property
    def user(self):
        """ Currenct logged in user instance

            :rtype: Record instance
        """
        if self._user is None:
            self._user = self.get_obj('res.users').read_records(self.uid)
        return self._user

    @property
    def registered_objects(self):
        """ Stores list of registered in ERP database objects
        """
        return self.services['object'].get_registered_objects()

    def connect(self, **kwargs):
        """ Connects to the server

            if any keyword arguments will be passed, new Proxy instnace
            will be created using folowing algorithm: get init args from
            self instance and update them with passed keyword arguments,
            and call Proxy class constructor passing result as arguments.

            :return: Id of user logged in
            :rtype: int
            :raises ERPProxyException: if wrong login or password
        """
        if kwargs:
            init_kwargs = self.get_init_args()
            init_kwargs.update(kwargs)
            return ERP_Proxy(**init_kwargs)

        # Get the uid
        uid = self.services['common'].login(self.dbname, self._username, self._pwd)

        if not uid:
            raise ERPProxyException("Bad login or password")

        return uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches

            :return: ID of user logged in
            :rtype: int
            :raises ERPProxyException: if wrong login or password
        """
        self.services.clean_cache()
        self._uid = None
        self._user = None
        self._uid = self.connect()
        return self._uid

    def execute(self, obj, method, *args, **kwargs):
        """Call method *method* on object *obj* passing all next
           positional and keyword (if available on server)
           arguments to remote method

           Note that passing keyword argments not available on
           OpenERp/Odoo server 6.0 and older

           :param obj: object name to call method for
           :type obj: string
           :param method: name of method to call
           :type method: string
           :return: result of RPC method call
        """
        # avoid sending context when it is set to None
        # because of it is problem of xmlrpc
        if 'context' in kwargs and kwargs['context'] is None:
            kwargs = kwargs.copy()
            del kwargs['context']
        return self.services['object'].execute(obj, method, *args, **kwargs)

    def execute_wkf(self, object_name, signal, object_id):
        """ Triggers workflow event on specified object

            :param object_name: send workflow signal for
            :type object_name: string
            :param signal: name of signal to send
            :type signal: string
            :param object_id: ID of document (record) to send signal to
            :type obejct_id: int
        """
        result_wkf = self.services['object'].exec_workflow(object_name, signal, object_id)
        return result_wkf

    def get_obj(self, object_name):
        """ Returns wraper around openERP object 'object_name' which is instance of Object

            :param object_name: name of an object to get wraper for
            :return: instance of Object which wraps choosen object
            :rtype: Object instance
        """
        return self.services['object'].get_obj(object_name)

    def __getitem__(self, name):
        """ Returns instance of Object with name 'name'
        """
        res = None
        try:
            res = self.get_obj(name)
        except ValueError:
            raise KeyError('Wrong object name')

        return res

    def get_init_args(self):
        """ Returns dictionary with init arguments which can be safely passed
            to class constructor
        """
        return dict(user=self._username,
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    protocol=self.protocol,
                    verbose=self.connection.verbose)

    @classmethod
    def to_url(cls, inst, **kwargs):
        """ Converts instance to url

            :param inst: instance to convert to init args
            :type inst: ERP_Proxy|dict
            :return: generated URL
            :rtype: str
        """
        url_tmpl = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s"
        if isinstance(inst, ERP_Proxy):
            return url_tmpl % inst.get_init_args()
        elif isinstance(inst, dict):
            return url_tmpl % inst
        elif inst is None and kwargs:
            return url_tmpl % kwargs
        else:
            raise ValueError("inst must be ERP_Proxy instance or dict")

    # TODO: think to reimplement as property
    def get_url(self):
        """ Returns dabase URL

            At this moment mostly used internaly in session
        """
        return self.to_url(self)

    def __str__(self):
        return "ERP_Proxy: %s" % self.get_url()
    __repr__ = __str__
