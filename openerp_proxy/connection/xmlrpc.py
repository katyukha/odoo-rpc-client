# python imports
from six.moves import xmlrpc_client as xmlrpclib

# project imports
from .connection import ConnectorBase
from ..utils import ustr
from .. import exceptions as exceptions


class XMLRPCError(exceptions.ConnectorError):
    def __init__(self, fault_instance):
        """ @param instance of xmlrpclib.Fault
        """
        msg = (u"A fault occured\n"
               u"Fault code: %s\n"
               u"Fault string: %s\n"
               u"" % (ustr(fault_instance.faultCode),
                      ustr(fault_instance.faultString)))
        msg = msg.encode('utf-8')
        super(XMLRPCError, self).__init__(msg)


class XMLRPCMethod(object):
    """ Class wrapper around XML-RPC method to wrap xmlrpclib.Fault
        into XMLRPCProxy
    """

    def __init__(self, method):
        self.__method = method

    def __getattr__(self, name):
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
    """
    class Meta:
        name = 'xml-rpc'

    def __init__(self, *args, **kwargs):
        super(ConnectorXMLRPC, self).__init__(*args, **kwargs)
        self.__services = {}

    def get_service_url(self, service_name):
        return 'http://%s:%s/xmlrpc/%s' % (self.host, self.port, service_name)

    def _get_service(self, name):
        service = self.__services.get(name, False)
        if service is False:
            service = XMLRPCProxy(self.get_service_url(name), verbose=self.verbose)
            self.__services[name] = service
        return service


class ConnectorXMLRPCS(ConnectorXMLRPC):
    """ XML-RPCS Connector
    """
    class Meta:
        name = 'xml-rpcs'

    def get_service_url(self, service_name):
        return 'https://%s:%s/xmlrpc/%s' % (self.host, self.port, service_name)
