from openerp_proxy.service.object import ObjectService

LOG_SIMPLE = False


class ObjectServiceLog(ObjectService):

    def execute(self, obj, method, *args, **kwargs):
        if LOG_SIMPLE:
            print("Execute [%s, %s]" % (obj, method))
        else:
            print("Execute [%s, %s] (%s, %s)" % (obj, method, args, kwargs))
        return super(ObjectServiceLog, self).execute(obj, method, *args, **kwargs)
