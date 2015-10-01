from ..service.object import ObjectService
from contextlib import contextmanager
import time


@contextmanager
def timeit_context(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))


LOG_SIMPLE = False


class ObjectServiceLog(ObjectService):
    """ Simply logs all calls to ``execute`` method of `object` service
        to console (displying all arguments).
        If module level variable ``LOG_SIMPLE`` set to True,then
        only simple lines like 'Execute [<obj>, <method>] will be displayed
    """

    def execute(self, obj, method, *args, **kwargs):
        if LOG_SIMPLE:
            msg = "Execute [%s, %s]" % (obj, method)
        else:
            msg = "Execute [%s, %s] (%s, %s)" % (obj, method, args, kwargs)
        with timeit_context(msg):
            return super(ObjectServiceLog, self).execute(obj, method, *args, **kwargs)
