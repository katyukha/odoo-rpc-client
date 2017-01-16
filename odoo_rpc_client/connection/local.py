# python imports
import os
import logging
import atexit
import functools

# project imports
from .connection import ConnectorBase
from ..exceptions import ConnectorError
from ..utils import ustr


logger = logging.getLogger(__name__)


class LocalConnectorError(ConnectorError):
    """ Local connector error wrapper
    """
    def __init__(self, exc):
        self.exc = exc
        super(LocalConnectorError, self).__init__(ustr(exc))


class LocalMethod(object):
    """ Odoo method wrapper
    """
    def __init__(self, service, name):
        self.service = service
        self.name = name
        self.odoo = service.odoo

        # bind odoo's methdo to self._method
        if self.odoo._api_v7:
            self._method = functools.partial(
                self.odoo.netsvc.ExportService.getService(
                    self.service.service_name).dispatch,
                self.name)
        else:
            self._method = functools.partial(
                self.odoo.http.dispatch_rpc,
                self.service.service_name,
                self.name)

    def __call__(self, *args):
        try:
            res = self._method(args)
        except Exception as exc:
            raise LocalConnectorError(exc)
        return res


class LocalService(object):
    """ Local Odoo service
    """
    def __init__(self, connection, service_name):
        self.connection = connection
        self.service_name = service_name
        self.odoo = connection.odoo

        # variable to cache methods
        self._methods = {}

    def __getattr__(self, name):
        meth = self._methods.get(name, None)
        if meth is None:
            try:
                meth = LocalMethod(self, name)
            except KeyError as exc:
                raise LocalConnectorError(exc)
            except AttributeError as exc:
                raise LocalConnectorError(exc)
            except Exception as exc:
                raise LocalConnectorError(exc)
            else:
                self._methods[name] = meth

        return meth


class ConnectorLocal(ConnectorBase):
    """ Connect to local odoo instal.

        NOTE: To use this connector, odoo must be importable as 'odoo' or
              'openerp'. This connector will automaticaly determine
              Odoo version, and organize correct bechavior

        NOTE2: This connector tested only on **python2.7** because
               Odoo uses this version of python

        NOTE3: Because, standard params have no sense for this connector,
               it ignores them, but instead, it looks in extra_args
               for argument 'local_args', which must be a list of command_line
               args to run odoo with
    """
    class Meta:
        name = 'local'

    # Need for backward compatability, because there 'verbose' keyword argument
    # may be present in extra_args due to old sessions saved with this arg
    def __init__(self, *args, **kwargs):
        super(ConnectorLocal, self).__init__(*args, **kwargs)
        self.extra_args.pop('verbose', None)

        self.odoo_args = self.extra_args.get('local_args', [])

        self.odoo = self._start_odoo_services()

    # This code is based on erppeek's code:
    #     https://github.com/tinyerp/erppeek/blob/master/erppeek.py#L251
    def _start_odoo_services(self):
        """Initialize the Odoo services.
           return `odoo` package
        """
        try:
            # Odoo 10.0+
            import odoo
        except ImportError:
            try:
                # Odoo 9.0 and less versions
                import openerp as odoo
            except ImportError:
                raise

        if getattr(odoo, '_odoo_services_started', False):
            # If odoo services already started, just return odoo instance
            return odoo

        if odoo.release.version_info < (7,):
            raise ConnectorError(
                "Unsupported Odoo version: %s" % odoo.release.version_info)

        odoo._api_v7 = odoo.release.version_info < (8,)
        os.putenv('TZ', 'UTC')
        odoo.tools.config.parse_config(self.odoo_args)

        if odoo._api_v7:
            odoo.service.start_internal()
        else:   # Odoo v8
            try:
                odoo.api.Environment._local.environments = \
                    odoo.api.Environments()
            except AttributeError:
                pass

        def close_all():
            for db in odoo.modules.registry.RegistryManager.registries.keys():
                odoo.sql_db.close_db(db)
        atexit.register(close_all)

        # Mark odoo, that it have services started
        odoo._odoo_services_started = True

        return odoo

    def _get_service(self, name):
        return LocalService(self, name)
