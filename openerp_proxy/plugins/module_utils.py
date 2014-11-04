from openerp_proxy.plugin import Plugin


class ModuleUtils(Plugin):

    class Meta:
        name = "module_utils"

    def __init__(self, *args, **kwargs):
        super(ModuleUtils, self).__init__(*args, **kwargs)
        self._modules = None

    @property
    def modules(self):
        """ Returns dictionary of modules registered in system
            dict is like: {'module_name': module_inst}
            where module_inst i browse_record instance for this module
        """
        if self._modules is None:
            self._modules = {m.name: m for m in self.proxy['ir.module.module'].search_records([])}
        return self._modules

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
