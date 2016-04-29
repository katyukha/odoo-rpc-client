# python imports
from six.moves import xmlrpc_client as xmlrpclib

# project imports
from .connection import ConnectorBase
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


class XMLRPCProxy(xmlrpclib.ServerProxy):
    """ Wrapper class around XML-RPC's ServerProxy to wrap method's errors
        into XMLRPCError class
    """
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
        return XMLRPCProxy(self.get_service_url(name), **self.extra_args)


class ConnectorXMLRPCS(ConnectorXMLRPC):
    """ XML-RPCS Connector

        Note: extra_arguments may be same as parametrs of xmlrpclib.ServerProxy
    """
    class Meta:
        name = 'xml-rpcs'
        ssl = True
