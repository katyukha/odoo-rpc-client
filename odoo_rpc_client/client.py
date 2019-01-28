# -*- coding: utf8 -*-
# Copyright © 2014-2018 Dmytro Katyukha <dmytro.katyukha@gmail.com>

#######################################################################
# This Source Code Form is subject to the terms of the Mozilla Public #
# License, v. 2.0. If a copy of the MPL was not distributed with this #
# file, You can obtain one at http://mozilla.org/MPL/2.0/.            #
#######################################################################

"""
This module provides some classes to simplify access to Odoo server via xmlrpc.

Example ussage of this module

.. code:: python

    >>> cl = Client('server.com', 'dbname', 'some_user', 'mypassword')
    >>> sale_obj = cl['sale_order']
    >>> sale_ids = sale_obj.search([('state','not in',['done','cancel'])])
    >>> sale_data = sale_obj.read(sale_ids, ['name'])
    >>> for order in sale_data:
    ...     print("%5s :    %s" % (order['id'],order['name']))
    >>> product_tmpl_obj = cl['product.template']
    >>> product_obj = cl['product.product']
    >>> tmpl_ids = product_tmpl_obj.search([('name','ilike','template_name')])
    >>> print(product_obj.search([('product_tmpl_id','in',tmpl_ids)]))

    >>> db = Client('erp.host.com', 'dbname='db0', user='your_user')
    >>> so = db['sale.order']
    >>> order_ids = so.search([('state','=','done')])
    >>> order = so.read(order_ids[0])

Also You can call any method (beside private
ones starting with underscore(_)) of any model.
For example following code allows to check
availability of stock moves:

.. code:: python

    >>> db = session.connect()
    >>> move_obj = db['stock.move']
    >>> move_ids = [1234] # IDs of stock moves to be checked
    >>> move_obj.check_assign(move_ids)

Ability to use Record class as analog to browse_record:

.. code:: python

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

import six
import re
from extend_me import Extensible
from pkg_resources import parse_version

# project imports
from .connection import get_connector, DEFAULT_TIMEOUT
from .exceptions import LoginException
from .service import ServiceManager
from .plugin import PluginManager

# Enable ORM features
from . import orm  # noqa


__all__ = ('Client',)

RE_CLIENT_URL = re.compile(
    r"(?:(?P<protocol>[\w\-]+)\:\/\/)?(?:(?P<user>[\w\-]+)?"
    r"(?:\:(?P<pwd>[\w\-\.\,]+))?\@)?"
    r"(?P<host>[\w\-\.]+)(?:\:(?P<port>\d{2,5}))?\/"
    r"(?P<dbname>[\w\-.]+)?$")


@six.python_2_unicode_compatible
class Client(Extensible):
    """
       A simple class to connect to Odoo instance via RPC (XML-RPC, JSON-RPC)
       Should be initialized with following arguments:

       :param str host: server host name to connect to
       :param str dbname: name of database to connect to
       :param str user: username to login as
       :param str pwd: password to log-in with
       :param int port: port number of server
       :param str protocol: protocol used to connect.
                            To get list of available protcols call:
                            ``odoo_rpc_client.connection.get_connector_names()``
       :param float timeout: Connection timeout

       any other keyword arguments will be directly passed to connector

       Example::

           >>> db = Client('host', 'dbname', 'user', pwd='Password')
           >>> cl = Client('host')
           >>> db2 = cl.login('dbname', 'user', 'password')

       Allows access to Odoo objects / models via dictionary syntax::

           >>> db['sale.order']
               Object ('sale.order')
    """

    def __init__(self, host, dbname=None, user=None, pwd=None, port=8069,
                 protocol='xml-rpc', timeout=DEFAULT_TIMEOUT, **extra_args):
        self._dbname = dbname
        self._username = user
        self._pwd = pwd

        self._connection = get_connector(protocol)(
            host, port, timeout, extra_args)
        self._services = ServiceManager(self)
        self._plugins = PluginManager(self)

        self._uid = None
        self._user = None
        self._user_context = None
        self._database_version_full = None

    @property
    def dbname(self):
        """ Name of database to connect to

            :rtype: str
        """
        return self._dbname

    @property
    def username(self):
        """ User login used to access DB

            :rtype: str
        """
        return self._username

    @property
    def host(self):
        """ Server host

            :rtype: str
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

            :rtype: str
        """
        return self._connection.Meta.name

    @property
    def services(self):
        """ ServiceManager instance, which contains list
            of all available services for current connection.

            :rtype: odoo_rpc_client.service.service.ServiceManager

            Usage examples::

                db.services.report   # report service
                db.services.object   # object service (model related actions)
                db.services.common   # used for login
                                     # (db.services.common.login(dbname,
                                     #                           username,
                                     #                           password)
                db.services.db       # database management service

        """
        return self._services

    @property
    def plugins(self):
        """ Plugins associated with this Client instance

            :rtype: odoo_rpc_client.plugin.PluginManager

            Usage examples::

                db.plugins.module_utils    # access module_utils plugin
                db.plugins['module_utils]  # access module_utils plugin

        """
        return self._plugins

    @property
    def connection(self):
        """ Connection to server.

            :rtype: odoo_rpc_client.connection.connection.ConnectorBase
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

            :rtype: odoo_rpc_client.orm.record.Record
        """
        if self._user is None:
            self._user = self.get_obj('res.users').read_records(self.uid)
        return self._user

    @property
    def user_context(self):
        """ Get current user context

            :rtype: dict
        """
        if self._user_context is None:
            self._user_context = self.get_obj('res.users').context_get()
        return self._user_context

    @property
    def server_version(self):
        """ Server base version  ('8.0', '9.0', etc)

            (Already parsed with ``pkg_resources.parse_version``)
        """
        return self.services.db.server_base_version()

    @property
    def database_version_full(self):
        """ Full database base version ('9.0.1.3', etc)

            (Already parsed with ``pkg_resources.parse_version``)
        """
        if self._database_version_full is None:
            base_module = self.get_obj('ir.module.module').search_records(
                [('name', '=', 'base')])[0]
            self._database_version_full = parse_version(
                base_module.installed_version)
        return self._database_version_full

    @property
    def database_version(self):
        """ Base database version ('8.0', '9.0', etc)

            (Already parsed with ``pkg_resources.parse_version``)
        """
        return parse_version(
            '.'.join(
                self.database_version_full.base_version.split('.', 2)[:2]))

    @property
    def registered_objects(self):
        """ List of registered in Odoo database objects

            :rtype: list
        """
        return self.services['object'].get_registered_objects()

    def login(self, dbname, user, password):
        """ Login to database

            Return new Client instance.
            (Just an aliase on ``connect`` method)

            :param str dbname: name of database to connect to
            :param str user: username to login as
            :param str password: password to log-in with
            :return: new Client instance, with specifed credentials
            :rtype: odoo_rpc_client.client.Client
        """
        return self.connect(dbname=dbname, user=user, pwd=password)

    def connect(self, **kwargs):
        """ Connects to the server

            if any keyword arguments will be passed, new Proxy instnace
            will be created using folowing algorithm: get init args from
            self instance and update them with passed keyword arguments,
            and call Proxy class constructor passing result as arguments.

            **Note**, that if You pass any keyword arguments,
            You also should pass 'pwd' keyword argument with user password

            :return: Id of user logged in or new Client
                     instance (if kwargs passed)
            :rtype: int|Client
            :raises LoginException: if wrong login or password
        """
        if kwargs:
            init_kwargs = self.get_init_args()
            init_kwargs.update(kwargs)

            return Client(**init_kwargs)

        # Get the uid
        if not self._pwd or not self.username or not self.dbname:
            raise LoginException("User login and password and dbname required "
                                 "for this operation")

        uid = self.services['common'].login(self.dbname,
                                            self.username,
                                            self._pwd)

        if not uid:
            raise LoginException("Bad login or password")

        return uid

    def reconnect(self):
        """ Recreates connection to the server and clears caches

            :return: ID of user logged in
            :rtype: int
            :raises ClientException: if wrong login or password
        """
        self.services.clean_cache()
        self._uid = None
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
        result_wkf = self.services['object'].execute_wkf(object_name,
                                                         signal,
                                                         object_id)
        return result_wkf

    def get_obj(self, object_name):
        """ Returns wraper around Odoo object 'object_name'
            which is instance of orm.object.Object class

            :param object_name: name of an object to get wraper for
            :return: instance of Object which wraps choosen object
            :rtype: odoo_rpc_client.orm.object.Object
        """
        return self.services['object'].get_obj(object_name)

    def ref(self, xmlid):
        """ Return record for specified xmlid

            :param str xmlid: string representing xmlid to get record for.
                              xmlid must be *fully qualified*
                              (with module name)
            :return: Record for that xmlid or False
            :rtype: odoo_rpc_client.orm.record.Record
        """
        try:
            module, name = xmlid.split('.')
        except ValueError:
            raise ValueError(
                "Fully qualified xmlid required! (Ex. 'module_name.xmlid'")
        res = self['ir.model.data'].search_records(
            [('module', '=', module), ('name', '=', name)],
            limit=1)
        if res:
            res = res[0]
            return self[res.model].read_records(res.res_id)

        return False

    def __getitem__(self, name):
        """ Returns instance of Object with name 'name'
        """
        res = None
        try:
            res = self.get_obj(name)
        except ValueError:
            raise KeyError('Wrong object/model name: %s' % name)

        return res

    def get_init_args(self):
        """ Returns dictionary with init arguments which can be safely passed
            to class constructor

            :rtype: dict
        """
        return dict(user=self.username,
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    protocol=self.protocol,
                    **self.connection.extra_args)

    @classmethod
    def to_url(cls, inst, **kwargs):
        """ Converts instance to url

            :param inst: instance to convert to init args
            :type inst: Client|dict
            :return: generated URL
            :rtype: str
        """
        url_tmpl = "%(protocol)s://%(user)s@%(host)s:%(port)s/%(dbname)s"
        if isinstance(inst, Client):
            return url_tmpl % inst.get_init_args()
        elif isinstance(inst, dict):
            return url_tmpl % inst
        elif inst is None and kwargs:
            return url_tmpl % kwargs
        else:
            raise ValueError("inst must be Client instance or dict")

    @classmethod
    def from_url(cls, url):
        """ Create Client instance from URL

            :param str url: url of Client
            :return: Client instance
            :rtype: Client
        """
        m = RE_CLIENT_URL.match(url)
        if m:
            data = dict(m.groupdict())
            data['protocol'] = data.get('protocol', None) or 'xml-rpc'
            data['port'] = int(data.get('port', None) or '80')
            return Client(**data)
        raise ValueError("Cannot parse url")

    # TODO: think to reimplement as property
    def get_url(self):
        """ Returns dabase URL

            At this moment mostly used internaly in session
        """
        return self.to_url(self)

    def clean_caches(self):
        """ Clean client related caches
        """
        self.services.clean_service_caches()
        self.plugins.refresh()
        self._user_context = None
        self._user = None
        self._database_version_full = None

    def __str__(self):
        return u"Client: %s" % self.get_url()

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Client):
            return self.get_url() == other.get_url()
        else:
            return False

    def _ipython_key_completions_(self):
        return self.services['object'].get_registered_objects()
