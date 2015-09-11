# Python imports
import six
import extend_me

from .utils import DirMixIn

PluginMeta = extend_me.ExtensibleByHashType._('Plugin', hashattr='name')


class Plugin(six.with_metaclass(PluginMeta)):
    """ Base class for all plugins, extensible by name

        (uses metaclass extend_me.ExtensibleByHashType)

        :param erp_proxy: instance of Client to bind plugins to
        :type erp_proxy: openerp_proxy.core.Client instance

        Example of simple plugin::

            from openerp_proxy.plugin import Plugin

            class AttandanceUtils(Plugin):

                # This is required to register Your plugin
                # *name* - is for db.plugins.<name>
                class Meta:
                    name = "attendance"

                def get_sign_state(self):
                    # Note: folowing code works on version 6 of Openerp/Odoo
                    emp_obj = self.proxy['hr.employee']
                    emp_id = emp_obj.search([('user_id', '=', self.proxy.uid)])
                    emp = emp_obj.read(emp_id, ['state'])
                    return emp[0]['state']

        This plugin will automaticaly register itself in system, when module which contains it will be imported.
    """

    def __init__(self, erp_proxy):
        self._erp_proxy = erp_proxy

    @property
    def proxy(self):
        """ Related Client instance
        """
        return self._erp_proxy

    def __repr__(self):
        try:
            name = self.Meta.name
        except AttributeError:
            name = None

        if name is not None:
            return 'openerp_proxy.plugin.Plugin:%s' % name
        return super(Plugin, self).__repr__()


class TestPlugin(Plugin):
    """ Jusn an example plugin to test if plugin logic works
    """

    class Meta:
        name = 'Test'

    def test(self):
        return self.proxy.get_url()


class PluginManager(extend_me.Extensible, DirMixIn):
    """ Class that holds information about all plugins

        :param erp_proxy: instance of Client to bind plugins to
        :type erp_proxy: openerp_proxy.core.Client instance

        Plugiins will be accessible via index or attribute syntax::

            plugins = PluginManager(proxy)
            plugins.Test   # acceps plugin 'Test' as attribute
            plugins['Test']  # access plugin 'Test' via indexing
    """
    def __init__(self, erp_proxy):
        """
        """
        self.__erp_proxy = erp_proxy
        self.__plugins = {}

    def __getitem__(self, name):
        plugin = self.__plugins.get(name, False)
        if plugin is False:
            try:
                pluginCls = type(Plugin).get_class(name)
            except ValueError as e:
                raise KeyError(str(e))

            plugin = pluginCls(self.__erp_proxy)
            self.__plugins[name] = plugin
        return plugin

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __contains__(self, name):
        return name in self.registered_plugins

    def __dir__(self):
        res = super(PluginManager, self).__dir__()
        res.extend(self.registered_plugins)
        return res

    @property
    def registered_plugins(self):
        """ List of names of registered plugins
        """
        return type(Plugin).get_registered_names()

    def refresh(self):
        """ Clean-up plugin cache
            This will force to reinitialize each plugin when asked
        """
        self.__plugins = {}
        return self


