from openerp_proxy.service.service import ServiceBase
from openerp_proxy.exceptions import ConnectorError


class ObjectService(ServiceBase):
    """ Service class to simplify interaction with 'object' service
        Particulary, implements logic of choosing execute method ('execute' or 'execute_kw')
        The last one cannot work with keyword arguments(
    """
    class Meta:
        name = 'object'

    def __init__(self, *args, **kwargs):
        super(ObjectService, self).__init__(*args, **kwargs)
        self.__use_execute_kw = None
        self.__registered_objects = None

    @property
    def use_execute_kw(self):
        """ Checks whether 'execute_kw' method is available or not
        """
        if self.__use_execute_kw is None:
            try:
                self._service.execute_kw(self.proxy.dbname, self.proxy.uid, self.proxy.pwd, 'ir.model', 'search', ([],), dict(limit=1))
                self.__use_execute_kw = True
            except ConnectorError:
                self.__use_execute_kw = False
        return self.__use_execute_kw

    def execute(self, obj, method, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        if self.use_execute_kw:
            result = self._service.execute_kw(self.proxy.dbname, self.proxy.uid, self.proxy.pwd, obj, method, args, kwargs)
        else:
            result = self._service.execute(self.proxy.dbname, self.proxy.uid, self.proxy.pwd, obj, method, *args, **kwargs)

        return result

    def execute_wkf(self, object_name, signal, object_id):
        """ Triggers workflow event on specified object
        """
        result_wkf = self._service.exec_workflow(self.proxy.dbname, self.proxy.uid, self.proxy.pwd, object_name, signal, object_id)
        return result_wkf

    def get_registered_objects(self):
        """ Returns list of registered objects in database
        """
        if self.__registered_objects is not None:
            return self.__registered_objects
        ids = self.execute('ir.model', 'search', [])
        read = self.execute('ir.model', 'read', ids, ['model'])
        self.__registered_objects = [x['model'] for x in read]
        return self.__registered_objects

    def clean_caches(self):
        """ Cleans caches, to fill them with fresh data with next call of related methods
        """
        self.__use_execute_kw = None
        self.__registered_objects = None

