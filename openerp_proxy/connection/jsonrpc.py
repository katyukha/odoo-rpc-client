# python imports
import six
import json
import random
import requests
import logging

# project imports
from .connection import ConnectorBase
from .. import exceptions as exceptions
from ..utils import ustr


logger = logging.getLogger(__name__)


@six.python_2_unicode_compatible
class JSONRPCError(exceptions.ConnectorError):
    def __init__(self, message, code=None, data=None):
        self.message = message
        self.code = code
        self.data = data

    def __str__(self):
        if self.data is None:
            return self.message

        if self.data.get('message', False) and self.data.get('debug', False):
            res_tmpl = u"""%(message)s\n%(debug)s\n"""
            return res_tmpl % self.data

        return ustr(self.data)


# TODO: think, may be it is a good idea to reimplement this via functions
class JSONRPCMethod(object):
    """ Class that implements RPC call via json-rpc protocol
    """
    __slots__ = ('__method', '__url', '__service', '__rpc_proxy')

    def __init__(self, rpc_proxy, url, service, method):
        self.__method = method
        self.__url = url
        self.__service = service
        self.__rpc_proxy = rpc_proxy

    def prepare_method_data(self, *args):
        """ Prepare data for JSON request
        """
        return {
            "jsonrpc": "2.0",
            "method": 'call',
            "params": {
                "service": self.__service,
                "method": self.__method,
                "args": args,
            },
            "id": random.randint(0, 1000000000),
        }

    def __call__(self, *args):
        data = json.dumps(self.prepare_method_data(*args))
        # Call rpc
        try:
            res = requests.post(self.__url, data=data, headers={
                "Content-Type": "application/json",
            }, verify=self.__rpc_proxy.ssl_verify)
        except requests.exceptions.RequestException as exc:
            msg = ("Cannot connect to url %s\n"
                   "Exception %s raised!" % (self.__url, exc))
            logger.error(msg)
            raise JSONRPCError(msg)

        # Process results
        try:
            result = json.loads(res.text)
        except ValueError:
            info = {
                "original_url": self.__url,
                "url": res.url,
                "code": res.status_code,
                "content": res.text[:2000],
            }
            logger.error("Cannot decode JSON")
            raise JSONRPCError("Cannot decode JSON: %s" % info)

        if result.get("error", None):
            error = result['error']
            raise JSONRPCError(error['message'],
                               code=error.get('code', None),
                               data=error.get('data', None))
        # if 'result' is not present in response object, then it seems, that
        # result is None
        return result.get("result", None)


class JSONRPCProxy(object):
    """ Wrapper class around XML-RPC's ServerProxy to wrap method's errors
        into XMLRPCError class
    """
    def __init__(self, host, port, service, ssl=False, ssl_verify=True):
        self.host = host
        self.port = port
        self.service = service

        addr = host
        if port not in (None, 80):
            addr += ':%s' % self.port
        self.url = '%s://%s/jsonrpc' % (ssl and 'https' or 'http', addr)

        # request parametrs
        self.ssl_verify = ssl_verify

        # variable to cach methods
        self._methods = {}

    def __getattr__(self, name):
        meth = self._methods.get(name, None)
        if meth is None:
            self._methods[name] = meth = JSONRPCMethod(self,
                                                       self.url,
                                                       self.service,
                                                       name)
        return meth


class ConnectorJSONRPC(ConnectorBase):
    """ JSON-RPC connector

        available extra arguments:
            - ssl_verify: (optional) if True, the SSL cert will be verified.
    """
    class Meta:
        name = 'json-rpc'
        use_ssl = False

    # Need for backward compatability, because there 'verbose' keyword argument
    # may be present in extra_args due to old sessions saved with this arg
    def __init__(self, *args, **kwargs):
        super(ConnectorJSONRPC, self).__init__(*args, **kwargs)
        self.extra_args.pop('verbose', None)

    def _get_service(self, name):
        return JSONRPCProxy(self.host,
                            self.port,
                            name,
                            ssl=self.Meta.use_ssl,
                            **self.extra_args)


class ConnectorJSONRPCS(ConnectorJSONRPC):
    """ JSON-RPCS Connector
    """
    class Meta:
        name = 'json-rpcs'
        use_ssl = True
