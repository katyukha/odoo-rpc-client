# Python imports

import extend_me


class Plugin(object):
    """ Base class for all plugins, extensible by name
        using extend_me.ExtensibleByHashType for it
    """
    __metaclass__ = extend_me.ExtensibleByHashType._('Plugin', hashattr='name')

    def __init__(self, erp_proxy):
        self._erp_proxy = erp_proxy

    @property
    def proxy(self):
        return self._erp_proxy


class TestPlugin(Plugin):
    """ Jusn an example plugin to test if plugin logic works
    """

    class Meta:
        name = 'Test'

    def test(self):
        print self.proxy.get_url()


class ERP_PluginManager(object):
    """ Class that holds information about all plugins
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
                raise KeyError(e.message)

            plugin = pluginCls(self.__erp_proxy)
            self.__plugins[name] = plugin
        return plugin

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __dir__(self):
        res = dir(super(ERP_PluginManager, self))
        res.extend(type(Plugin).get_registered_names())
        return res


