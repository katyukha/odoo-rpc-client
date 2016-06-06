from ..service.service import ServiceBase
from ..exceptions import ConnectorError


class ObjectService(ServiceBase):
    """ Service class to simplify interaction with 'object' service
        Particulary, implements logic of choosing execute method
        ('execute' or 'execute_kw') The last one cannot work with
        keyword arguments(
    """
    class Meta:
        name = 'object'

    def __init__(self, *args, **kwargs):
        super(ObjectService, self).__init__(*args, **kwargs)
        self.__use_execute_kw = None
        self._registered_objects = None

    @property
    def use_execute_kw(self):
        """ Checks whether 'execute_kw' method is available or not
        """
        if self.__use_execute_kw is None:
            try:
                self._service.execute_kw(self.client.dbname,
                                         self.client.uid,
                                         self.client._pwd,
                                         'ir.model',
                                         'search',
                                         ([],),
                                         dict(limit=1))
                self.__use_execute_kw = True
            except ConnectorError:  # pragma: no cover
                # Odoo version < 6.1
                self.__use_execute_kw = False
        return self.__use_execute_kw

    def execute(self, obj, method, *args, **kwargs):
        """First arguments should be 'object' and 'method' and next
           will be passed to method of given object
        """
        # avoid sending context when it is set to None
        # because of it is problem of xmlrpc
        if 'context' in kwargs and kwargs['context'] is None:
            kwargs = kwargs.copy()
            del kwargs['context']

        if self.use_execute_kw:
            result = self._service.execute_kw(self.client.dbname,
                                              self.client.uid,
                                              self.client._pwd,
                                              obj,
                                              method,
                                              args,
                                              kwargs)
        else:  # pragma: no cover
            result = self._service.execute(self.client.dbname,
                                           self.client.uid,
                                           self.client._pwd,
                                           obj,
                                           method,
                                           *args,
                                           **kwargs)

        return result

    def execute_wkf(self, object_name, signal, object_id):
        """ Triggers workflow event on specified object

            :param str object_name: name of object/model to trigger workflow on
            :param str signal: name of signal to send to workflow
            :param int object_id: ID of document (record) to send signal to
        """
        result_wkf = self._service.exec_workflow(self.client.dbname,
                                                 self.client.uid,
                                                 self.client._pwd,
                                                 object_name,
                                                 signal,
                                                 object_id)
        return result_wkf

    def _get_registered_objects(self):
        """ Implementation of get registered models (objects)
            Could be overridden by extensions
        """
        ids = self.execute('ir.model', 'search', [])
        read = self.execute('ir.model', 'read', ids, ['model'])
        return [x['model'] for x in read]

    def get_registered_objects(self):
        """ Returns list of registered objects in database
        """
        if self._registered_objects is not None:
            return self._registered_objects
        self._registered_objects = self._get_registered_objects()
        return self._registered_objects

    def clean_cache(self):
        """ Cleans service cache, to fill them with fresh data
            on next call of related methods
        """
        self.__use_execute_kw = None
        self._registered_objects = None
