# python imports
import json
import urllib2
import random

# project imports
from openerp_proxy.connection.connection import ConnectorBase
from openerp_proxy.utils import ustr
import openerp_proxy.exceptions as exceptions


class JSONRPCError(exceptions.ConnectorError):
    def __init__(self, message, code=None, data=None):
        self.message = message
        self.code = code
        self.data = data

    def __unicode__(self):
        if self.data is None:
            return self.message

        if self.data.get('message', False) and self.data.get('debug', False):
            res_tmpl = u"""%(message)s\n%(debug)s\n"""
            return res_tmpl % self.data

        return unicode(self.data)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def _repr_pretty_(self):
        return "TEST"


class JSONRPCMethod(object):
    """ Class wrapper around XML-RPC method to wrap xmlrpclib.Fault
        into XMLRPCProxy
    """

    def __init__(self, url, service, method):
        self.__method = method
        self.__url = url
        self.__service = service

    def __call__(self, *args):
        # TODO: add ability to use sessions
        data = {
            "jsonrpc": "2.0",
            "method": 'call',
            "params": {
                "service": self.__service,
                "method": self.__method,
                "args": args,
            },
            "id": random.randint(0, 1000000000),
        }
        req = urllib2.Request(url=self.__url, data=json.dumps(data), headers={
            "Content-Type": "application/json",
        })
        result = urllib2.urlopen(req)
        content = result.read()
        try:
            result = json.loads(content)
        except ValueError:
            info = {
                "original_url": self.__url,
                "url": result.geturl(),
                "info": result.info(),
                "code": result.getcode(),
                "content": content,
            }
            raise JSONRPCError("Cannot decode JSON: %s" % info)

        if result.get("error", None):
            error = result['error']
            raise JSONRPCError(error['message'],
                               code=error.get('code', None),
                               data=error.get('data', None))
        return result["result"]


class JSONRPCProxy(object):
    """ Wrapper class around XML-RPC's ServerProxy to wrap method's errors
        into XMLRPCError class
    """
    def __init__(self, host, port, service, ssl=False):
        self.host = host
        self.port = port
        self.service = service
        addr = (host if port is None else "%s:%s" % (self.host, self.port))
        self.url = '%s://%s/jsonrpc' % (ssl and 'https' or 'http', addr)

    def __getattr__(self, name):
        return JSONRPCMethod(self.url, self.service, name)


class ConnectorJSONRPC(ConnectorBase):
    """ JSON-RPC connector
    """
    class Meta:
        name = 'json-rpc'
        use_ssl = False

    def __init__(self, *args, **kwargs):
        super(ConnectorJSONRPC, self).__init__(*args, **kwargs)
        self.__services = {}

    def _get_service(self, name):
        service = self.__services.get(name, False)
        if service is False:
            service = JSONRPCProxy(self.host, self.port, name, ssl=self.Meta.use_ssl)
            self.__services[name] = service
        return service


class ConnectorJSONRPCS(ConnectorJSONRPC):
    """ JSON-RPCS Connector
    """
    class Meta:
        name = 'json-rpcs'
        use_ssl = True
