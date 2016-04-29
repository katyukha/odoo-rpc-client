# Python imports
import six
import extend_me

from .utils import DirMixIn

PluginMeta = extend_me.ExtensibleByHashType._('Plugin', hashattr='name')


@six.python_2_unicode_compatible
class Plugin(six.with_metaclass(PluginMeta)):
    """ Base class for all plugins, extensible by name

        (uses metaclass extend_me.ExtensibleByHashType)

        :param client: instance of Client to bind plugins to
        :type client: openerp_proxy.core.Client instance

        Example of simple plugin::

            from openerp_proxy.plugin import Plugin

            class AttandanceUtils(Plugin):

                # This is required to register Your plugin
                # *name* - is for db.plugins.<name>
                class Meta:
                    name = "attendance"

                def get_sign_state(self):
                    # Note: folowing code works on version 6 of Openerp/Odoo
                    emp_obj = self.client['hr.employee']
                    emp_id = emp_obj.search(
                        [('user_id', '=', self.client.uid)])
                    emp = emp_obj.read(emp_id, ['state'])
                    return emp[0]['state']

        This plugin will automaticaly register itself in system,
        when module which contains it will be imported.
    """

    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        """ Related Client instance
        """
        return self._client

    def __str__(self):
        return u"openerp_proxy.plugin.Plugin:%s" % self.Meta.name

    def __repr__(self):
        return u"<%s>" % (str(self))


class TestPlugin(Plugin):
    """ Jusn an example plugin to test if plugin logic works
    """

    class Meta:
        name = 'Test'

    def test(self):
        return self.client.get_url()


@six.python_2_unicode_compatible
class PluginManager(extend_me.Extensible, DirMixIn):
    """ Class that holds information about all plugins

        :param client: instance of Client to bind plugins to
        :type client: openerp_proxy.core.Client instance

        Plugiins will be accessible via index or attribute syntax::

            plugins = PluginManager(client)
            plugins.Test   # acceps plugin 'Test' as attribute
            plugins['Test']  # access plugin 'Test' via indexing
    """
    def __init__(self, client):
        """
        """
        self.__client = client
        self.__plugins = {}

    def __getitem__(self, name):
        plugin = self.__plugins.get(name, False)
        if plugin is False:
            try:
                pluginCls = type(Plugin).get_class(name)
            except ValueError as e:
                raise KeyError(str(e))

            plugin = pluginCls(self.__client)
            self.__plugins[name] = plugin
        return plugin

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __contains__(self, name):
        return name in self.registered_plugins

    def __iter__(self):
        return iter(self.registered_plugins)

    def __len__(self):
        return len(self.registered_plugins)

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

    def __str__(self):
        return u"openerp_proxy.plugin.PluginManager [%d]" % len(self)

    def __repr__(self):
        return u"<%s>" % str(self)
