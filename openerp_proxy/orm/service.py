from openerp_proxy.service.object import ObjectService
from openerp_proxy.orm.object import Object


class Service(ObjectService):
    """ Service class to simplify interaction with 'object' service
        Particulary, implements logic of choosing execute method ('execute' or 'execute_kw')
        The last one cannot work with keyword arguments(
    """

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)
        self.__objects = {}   # cached objects

    def get_obj(self, object_name):
        """ Returns wraper around OpenERP object 'object_name' which is instance of ERP_Object

            @param object_name: name of an object to get wraper for
            @return: instance of ERP_Object which wraps choosen object
        """
        if object_name in self.__objects:
            return self.__objects[object_name]

        if object_name not in self.get_registered_objects():
            raise ValueError("There is no object named '%s' in ERP" % object_name)

        obj = Object(self, object_name)
        self.__objects[object_name] = obj
        return obj

    def clean_caches(self):
        """ Cleans caches, to fill them with fresh data with next call of related methods
        """
        super(Service, self).clean_caches()
        self.__objects = {}


