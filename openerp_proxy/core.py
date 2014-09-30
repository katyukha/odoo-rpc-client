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
    ... [12, 'OUT-12']
    >>> move.picking_id__obj.id
    ... 12
    >>> move.picking_id__obj.name
    ... 'OUT-12'
    >>> move.picking_id__obj.state
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

           >>> db = ERP_Proxy('dbname', 'host', 'user', pwd = 'Password', verbose = False)

       Allows access to ERP objects via dictionary syntax:

           >>> db['sale.order']
               Object ('sale.order')
    """

    def __init__(self, dbname, host, user, pwd, port=8069, protocol='xml-rpc', verbose=False):
        # TODO: hide these fields behide properties
        self.dbname = dbname
        self.host = host
        self.user = user  # TODO: rename. Use this name for property yo get logged in user record instace
        self.port = port
        self.pwd = pwd
        self.verbose = verbose
        self.protocol = protocol

        self._connection = None
        self._services = None

        self._uid = None

    @property
    def services(self):
        if self._services is None:
            self._services = ServiceManager(self)
        return self._services

    @property
    def connection(self):
        """ Automatically connects to OpenERP and returns
            connection instance
        """
        if self._connection is None:
            connector = get_connector(self.protocol)
            self._connection = connector(self.host, self.port, verbose=self.verbose)
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

            returns Id of user connected
        """
        # Get the uid
        uid = self.services['common'].login(self.dbname, self.user, self.pwd)

        if not uid:
            raise ERPProxyException("Bad login or password")

        return uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches
        """
        self._uid = self.connect()
        return self._uid

    def execute(self, obj, method, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        return self.services['object'].execute(obj, method, *args, **kwargs)

    def execute_wkf(self, object_name, signal, object_id):
        """ Triggers workflow event on specified object
        """
        result_wkf = self.services['object'].exec_workflow(object_name, signal, object_id)
        return result_wkf

    def get_obj(self, object_name):
        """ Returns wraper around openERP object 'object_name' which is instance of Object

            @param object_name: name of an object to get wraper for
            @return: instance of Object which wraps choosen object
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
        return "%(protocol)s://%(user)s@%(host)s:%(port)s/%(database)s" % dict(user=self.user,
                                                                               host=self.host,
                                                                               database=self.dbname,
                                                                               port=self.port,
                                                                               protocol=self.protocol)

    def __str__(self):
        return "ERP_Proxy: %s" % self.get_url()
    __repr__ = __str__
