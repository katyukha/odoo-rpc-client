from ..service.object import ObjectService
from .object import get_object

__all__ = ('Service',)


class Service(ObjectService):
    """ Service class to simplify interaction with 'object' service.
        Particulary, implements logic of choosing execute
        method ('execute' or 'execute_kw') to use.
        The last one cannot work with keyword arguments
    """

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)
        self.__objects = {}   # cached objects

    def get_obj(self, object_name):
        """ Returns wraper around Odoo object 'object_name'
            which is instance of Object

            :param object_name: name of an object to get wraper for
            :type object_name: string
            :return: instance of Object which wraps choosen object
            :rtype: Object
        """
        if object_name in self.__objects:
            return self.__objects[object_name]

        if object_name not in self.get_registered_objects():
            raise ValueError("There is no object named '%s'" % object_name)

        obj = get_object(self, object_name)
        self.__objects[object_name] = obj
        return obj

    def clean_cache(self):
        """ Cleans caches, to fill them with fresh data
            on next call of related methods
        """
        super(Service, self).clean_cache()
        self.__objects = {}
