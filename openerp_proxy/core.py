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
        # TODO: hide these fields behide properties
        self.dbname = dbname
        self.user = user  # TODO: rename. Use this name for property yo get logged in user record instace
        self.pwd = pwd

        self._connection = get_connector(protocol)(host, port, verbose=verbose)
        self._services = ServiceManager(self)

        self._uid = None

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
    def connection(self):
        """ Connection to server.
        """
        return self._connection

    @property
    def uid(self):
        """ Returns ID of current user. if one is None,
            connects to database and returns it
        """
        if self._uid is None:
            self._uid = self.connect()
        return self._uid

    @property
    def registered_objects(self):
        """ Stores list of registered in ERP database objects
        """
        return self.services['object'].get_registered_objects()

    def connect(self):
        """ Connects to the server

            :return: Id of user logged in
            :rtype: int
            :raises ERPProxyException: if wrong login or password
        """
        # Get the uid
        uid = self.services['common'].login(self.dbname, self.user, self.pwd)

        if not uid:
            raise ERPProxyException("Bad login or password")

        return uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches

            :return: ID of user logged in
            :rtype: int
            :raises ERPProxyException: if wrong login or password
        """
        self._uid = self.connect()
        return self._uid

    def execute(self, obj, method, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object

           :param obj: object name to call method for
           :type obj: string
           :param method: name of method to call
           :type method: string
        """
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

    # TODO: think to reimplement as property
    def get_url(self):
        """ Returns dabase URL

            At this moment mostly used internaly in session
        """
        return "%(protocol)s://%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=self.user,
                                                                               host=self.host,
                                                                               database=self.dbname,
                                                                               port=self.port,
                                                                               protocol=self.protocol)

    def __str__(self):
        return "ERP_Proxy: %s" % self.get_url()
    __repr__ = __str__
