# -*- coding: utf-8 -*-
# Copyright © 2014-2018 Dmytro Katyukha <dmytro.katyukha@gmail.com>

#######################################################################
# This Source Code Form is subject to the terms of the Mozilla Public #
# License, v. 2.0. If a copy of the MPL was not distributed with this #
# file, You can obtain one at http://mozilla.org/MPL/2.0/.            #
#######################################################################

# python imports
import six
from six.moves import xmlrpc_client as xmlrpclib
from six.moves import http_client as httplib

# project imports
from .connection import ConnectorBase, DEFAULT_TIMEOUT
from ..utils import ustr
from .. import exceptions as exceptions


class XMLRPCError(exceptions.ConnectorError):
    """ Exception raised on XMLRpc errors

        :param xmlrpclib.Fault fault_instance: exception raised by XMLRPC lib
    """
    def __init__(self, fault_instance):
        self._fault = fault_instance
        msg = (u"A fault occured\n"
               u"Fault code: %s\n"
               u"Fault string: %s\n"
               u"" % (ustr(fault_instance.faultCode),
                      ustr(fault_instance.faultString)))
        msg = msg.encode('utf-8')
        super(XMLRPCError, self).__init__(msg)

    @property
    def fault(self):
        """ Return xmlrpclib.Fault instance related to this error
        """
        return self._fault


class XMLRPCMethod(object):
    """ Class wrapper around XML-RPC method to wrap xmlrpclib.Fault
        into XMLRPCProxy
    """

    def __init__(self, method):
        self.__method = method

    def __getattr__(self, name):  # pragma: no cover
        return XMLRPCMethod(getattr(self.__method, name))

    def __call__(self, *args):
        try:
            res = self.__method(*args)
        except xmlrpclib.Fault as fault:
            raise XMLRPCError(fault)
        return res


if six.PY2:
    class _TimeoutTransport(xmlrpclib.Transport):
        def __init__(self, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
            xmlrpclib.Transport.__init__(self, *args, **kwargs)
            self.timeout = timeout

        def make_connection(self, host):
            # -- Based on original python code --
            #
            # return an existing connection if possible.  This allows
            # HTTP/1.1 keep-alive.
            if self._connection and host == self._connection[0]:
                return self._connection[1]

            # create a HTTP connection object from a host descriptor
            chost, self._extra_headers, x509 = self.get_host_info(host)
            # store the host argument along with the connection object
            self._connection = host, httplib.HTTPConnection(
                chost, timeout=self.timeout)
            return self._connection[1]
elif six.PY3:
    class _TimeoutTransport(xmlrpclib.Transport):
        def __init__(self, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
            super(_TimeoutTransport, self).__init__(*args, **kwargs)
            self.timeout = timeout

        def make_connection(self, host):
            # -- Based on original python code --
            #
            # return an existing connection if possible.  This allows
            # HTTP/1.1 keep-alive.
            if self._connection and host == self._connection[0]:
                return self._connection[1]

            # create a HTTP connection object from a host descriptor
            chost, self._extra_headers, x509 = self.get_host_info(host)
            # store the host argument along with the connection object
            self._connection = host, httplib.HTTPConnection(
                chost, timeout=self.timeout)
            return self._connection[1]
else:
    _TimeoutTransport = xmlrpclib.Transport


class XMLRPCProxy(xmlrpclib.ServerProxy):
    """ Wrapper class around XML-RPC's ServerProxy to wrap method's errors
        into XMLRPCError class
    """
    def __init__(self, uri, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
        transport = _TimeoutTransport(timeout=timeout, *args, **kwargs)
        kwargs['transport'] = transport
        xmlrpclib.ServerProxy.__init__(self, uri, *args, **kwargs)

    def __getattr__(self, name):
        res = xmlrpclib.ServerProxy.__getattr__(self, name)
        if isinstance(res, xmlrpclib._Method):
            res = XMLRPCMethod(res)
        return res


class ConnectorXMLRPC(ConnectorBase):
    """ XML-RPC connector

        Note: extra_arguments may be same as parametrs of xmlrpclib.ServerProxy
    """
    class Meta:
        name = 'xml-rpc'
        ssl = False

    def get_service_url(self, service_name):
        addr = self.host
        if self.port not in (None, 80):
            addr += ':%s' % self.port
        proto = 'https' if self.Meta.ssl else 'http'
        return '%s://%s/xmlrpc/%s' % (proto, addr, service_name)

    def _get_service(self, name):
        return XMLRPCProxy(
            self.get_service_url(name),
            timeout=self.timeout,
            **self.extra_args)


class ConnectorXMLRPCS(ConnectorXMLRPC):
    """ XML-RPCS Connector

        Note: extra_arguments may be same as parametrs of xmlrpclib.ServerProxy
    """
    class Meta:
        name = 'xml-rpcs'
        ssl = True
