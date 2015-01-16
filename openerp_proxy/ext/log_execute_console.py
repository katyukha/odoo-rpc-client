from openerp_proxy.service.object import ObjectService

LOG_SIMPLE = False


class ObjectServiceLog(ObjectService):
    """ Simply logs all calls to ``execute`` method of `object` service
        to console (displying all arguments).
        If module level variable ``LOG_SIMPLE`` set to True,then
        only simple lines like 'Execute [<obj>, <method>] will be displayed
    """

    def execute(self, obj, method, *args, **kwargs):
        if LOG_SIMPLE:
            print("Execute [%s, %s]" % (obj, method))
        else:
            print("Execute [%s, %s] (%s, %s)" % (obj, method, args, kwargs))
        return super(ObjectServiceLog, self).execute(obj, method, *args, **kwargs)
