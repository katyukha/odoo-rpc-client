""" Simple extension which makes all
``client.services.object.execute`` calls to be logged

*NOTE*: this exension is not included in ``openerp_proxy.ext.all``
so it should be enabled (imported) manualy

Also allows to measure tim spent on rpc calls

Ususaly used for debug and performance tests
"""

import time
import logging

from ..service.object import ObjectService


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TimeTracker(object):
    """ Context manager to track separatly total time that some request took
        and time spent on rpc queries.

        Example::

            with TimeTracker('my-code-block') as t:
                product = db._product_product.serch_records([], limit=400000)
            print("Query time: %s, Total time: %s" % (p.query_time,
                                                      p.total_time))
    """

    # TODO: implement query counter, which may be used for performance tests
    query_timers = {}

    @classmethod
    def start_timing(cls, name):
        """ Start timer named *name*

            :param str name: name of timer to be started
        """
        cls.query_timers[name] = 0.0

    @classmethod
    def get_query_times(cls, name):
        """ Get time spent for queries for timer named *name*

            :param str name: name of timer to be started
        """
        return cls.query_timers.get(name, 0.0)

    @classmethod
    def _update_times(cls, time):
        """ This method should be called internaly only.

            Updates all timers
        """
        for timer in cls.query_timers:
            cls.query_timers[timer] += time

    @classmethod
    def remove_timer(cls, name):
        """ Remove timer for timers list.
        """
        del cls.query_timers[name]

    def __init__(self, name):
        self.name = name
        self._result_time = None
        self._total_time = None
        self._start_time = None

    @property
    def query_time(self):
        """ Return current query time (if not finished) or total query time
        """
        if self._result_time is None:
            return self.get_query_times(self.name)
        return self._result_time

    @property
    def total_time(self):
        """ if not started, returns 0.0
            if started and not finished returns current time - start time
            if finished return total time (time finished - start time
        """
        if self._start_time is None:
            return 0.0

        if self._total_time is not None:
            return self._total_time

        return time.time() - self._start_time

    def __enter__(self):
        self._start_time = time.time()
        self.start_timing(self.name)
        return self

    def __exit__(self, type, value, tb):
        if type is not None:
            raise value
        self._result_time = self.query_time
        self._total_time = self.total_time
        self.remove_timer(self.name)


# If set to False, then all arguments of 'execute' methon will be printed,
# otherwise only first two arguments and time spent will be printed
LOG_SIMPLE = True


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

        startTime = time.time()
        res = super(ObjectServiceLog, self).execute(obj,
                                                    method,
                                                    *args,
                                                    **kwargs)
        elapsedTime = time.time() - startTime

        TimeTracker._update_times(elapsedTime)

        logger.info('{} finished in {} ms'.format(msg,
                                                  int(elapsedTime * 1000)))

        return res
