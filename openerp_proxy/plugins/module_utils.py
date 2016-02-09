from ..plugin import Plugin
from ..orm.object import Object


# Overriden to add shortcut for module update
class ModuleObject(Object):
    """ Add shortcut methods to 'ir.module.module' object / model
        to install or upgrade modules

        Also this methods will be available for Record instances too
    """

    # Apply this extension only to 'ir.module.module' Object / Model
    class Meta:
        name = 'ir.module.module'

    def upgrade(self, ids, context=None):
        """ Immediatly upgrades module
        """
        kwargs = {} if context is None else {'context': context}
        res = self.button_immediate_upgrade(ids, **kwargs)
        self.client.clean_caches()  # because new models may appear in DB, so registered_objects shoud be refreshed
        return res

    def install(self, ids, context=None):
        """ Immediatly install module
        """
        kwargs = {} if context is None else {'context': context}
        res = self.button_immediate_install(ids, **kwargs)
        self.client.clean_caches()  # because new models may appear in DB, so registered_objects shoud be refreshed
        return res


class ModuleUtils(Plugin):
    """ Utility plugin to simplify module management

        Allows to access Odoo module objects as attributes of this plugin:

        .. code:: python

            db.plugins.module_utils.m_stock  # this method supports IPython autocomplete

        or dictionary style access to modules:

        .. code:: python

            db.plugins.moduld_utils['stock']

        which is equivalent to

        .. code:: python

            db.get_obj('ir.module.module').search_records([('name','=','stock')])[0]

        Also autocomplete in IPython supported for this syntax
    """

    class Meta:
        name = "module_utils"

    def __init__(self, *args, **kwargs):
        super(ModuleUtils, self).__init__(*args, **kwargs)
        self._modules = None

    @property
    def modules(self):
        """ Returns dictionary of modules registered in system.

            Result dict is like: ``{'module_name': module_inst}``

            where *module_inst* is *Record* instance for this module
        """
        if self._modules is None:
            self._modules = {m.name: m for m in self.client['ir.module.module'].search_records([])}
        return self._modules

    def update_module_list(self):
        """ Update module list

            If there are some modules added to server,
            update list, to be able to installe them.
        """
        self._modules = None
        return self.client['ir.module.module'].update_list()

    def __dir__(self):
        res = dir(super(ModuleUtils, self))
        res.extend(['m_' + i for i in self.modules.keys()])
        return res

    def __getitem__(self, name):
        return self.modules[name]

    def __getattr__(self, name):
        if name.startswith('m_') and name[2:] in self.modules:
            return self.modules[name[2:]]
        raise AttributeError("No attribute %s in object %s" % (name, self))
