# Python imports
import os
import os.path
import sys
import imp


# TODO: add ability to use functions in plugin too
#       or may be simply use decorators to simulate initialization?


# TODO: Add plugin types:
#           - database extensions (available for ERP_Proxy instances)
#           - object extensions (available for ERP_Object instances)
#           - record extensions (available for ERP_Record instances)


class PluginInitError(Exception):
    pass


class ERP_Plugin(object):
    """ Class which performs all routines related to plugin loading

        Each plugin must be python module or python package placed anywhere on filesystem
        and having structure like:

            class MyPluginClass1(object):
                _name = 'my_class1'

                # Method to initialize each plugin class for concrete openerp
                # database
                def __init__(self, db):  # db is required argument passed by infrastructure
                    self.db = db

                ...

            # Plugin function should be implemented as decorator like
            def MyPluginFunc1(db):
                def my_func1():
                    ...
                MyPluginFunc1._name = 'my_func1'
                return my_func1

            # Method which returns information about plugin and classes it
            # provides.
            def plugin_init():
                return {'classes': [MyPluginClass1],
                        'name': 'MyPlugin'}
    """

    def __init__(self, erp_proxy, plugin_data):
        """ @param plugin_data: dictionary returned by plugin's 'plugin_init' method
        """
        self.__erp_proxy = erp_proxy
        self.__data = plugin_data
        self.name = plugin_data['name']

        self.__classes = {cls._name: cls for cls in plugin_data['classes']}
        self.__objects = {}

    def __getitem__(self, name):
        """ Try to search for initialized plugin class
            and if none found initialize it from classes
        """
        plugin_obj = self.__objects.get(name, False)
        if plugin_obj is False:
            plugin_class = self.__classes[name]
            try:
                plugin_obj = plugin_class(self.__erp_proxy)
            except Exception as exc:
                raise PluginInitError(exc)
            self.__objects[name] = plugin_obj
        return plugin_obj

    def __getattribute__(self, name):
        try:
            return super(ERP_Plugin, self).__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    def __dir__(self):
        return self.__classes.keys()


class ERP_PluginManager(object):
    """ Class that holds information about all plugins
    """

    # Dictionary to store information about all loaded plugins
    __plugins_data = {}

    def __init__(self, erp_proxy):
        """
        """
        self.__erp_proxy = erp_proxy
        self.__plugins = {}

    @classmethod
    def load_plugin(cls, path):
        """ Method that loads plugin information making able
            lazy loading of plugin instance
        """
        m_path, name = os.path.split(path)
        if m_path not in sys.path:
            sys.path.append(m_path)

        m_name, m_ext = os.path.splitext(name)
        if m_ext:
            assert m_ext in ('.py', '.pyc', '.pyo'), "Not python file: %s, (%s, %s, %s)" % (path, m_path, m_name, m_ext)

        module = __import__(m_name)
        plugin_data = module.plugin_init()

        if 'name' in plugin_data:
            plugin_name = plugin_data['name']
        else:
            plugin_name = m_name
            plugin_data['name'] = m_name

        cls.__plugins_data[plugin_name] = {'path': path,
                                           'data': plugin_data}

    @classmethod
    def get_plugins_info(cls):
        return {name: val['path'] for name, val in cls.__plugins_data.iteritems()}

    def __getitem__(self, name):
        plugin = self.__plugins.get(name, False)
        if plugin is False:
            plugin_data = self.__plugins_data[name]['data']
            plugin = ERP_Plugin(self.__erp_proxy, plugin_data)
            self.__plugins[name] = plugin
        return plugin

    def __getattribute__(self, name):
        try:
            return super(ERP_PluginManager, self).__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    def __dir__(self):
        res = dir(super(ERP_PluginManager, self))
        res.extend(self.__plugins_data.keys())
        return res

