# python imports
import json
import random
import requests
import logging

# project imports
from .connection import ConnectorBase
from .. import exceptions as exceptions
from ..utils import ustr


logger = logging.getLogger(__name__)


class JSONRPCError(exceptions.ConnectorError):
    """ JSON-RPC error wrapper
    """
    def __init__(self, message, code=None, data=None):
        self.message = message
        self.code = code
        self.data = data

        if self.data_message and self.data_debug:
            msg = u"""%(message)s\n%(debug)s\n""" % self.data
        elif self.data:
            msg = ustr(self.data)
        else:
            msg = self.message

        super(JSONRPCError, self).__init__(msg)

    @property
    def data_message(self):
        """ Error message got from Odoo server
        """
        if self.data:
            return self.data.get('message', None)

    @property
    def data_debug(self):
        """ Debug information got from Odoo server

            Usualy traceback
        """
        if self.data:
            return self.data.get('debug', None)


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
        method_data = self.prepare_method_data(*args)
        data = json.dumps(method_data)

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
                "method_data": method_data,
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
    """ Simple Odoo service proxy wrapper
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
