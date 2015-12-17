"""
"""

import six

from .utils import ustr as _

import operator

__all__ = ('SField', 'SF', 'PlaceHolder', 'F')


# List of operators, could be applied to SField instances
SUPPORTED_OPERATIONS = [
    '__abs__',
    '__add__',
    '__and__',
    '__concat__',
    '__contains__',
    '__delitem__',
    '__div__',
    '__eq__',
    '__floordiv__',
    '__ge__',
    '__getitem__',
    '__gt__',
    '__iadd__',
    '__iand__',
    '__iconcat__',
    '__idiv__',
    '__ifloordiv__',
    '__ilshift__',
    '__imod__',
    '__imul__',
    '__index__',
    '__inv__',
    '__invert__',
    '__ior__',
    '__ipow__',
    '__irshift__',
    '__isub__',
    '__itruediv__',
    '__ixor__',
    '__le__',
    '__lshift__',
    '__lt__',
    '__mod__',
    '__mul__',
    '__ne__',
    '__neg__',
    '__not__',
    '__or__',
    '__pos__',
    '__pow__',
    '__rshift__',
    '__setitem__',
    '__sub__',
    '__truediv__',
    '__xor__',
]


@six.python_2_unicode_compatible
class PlaceHolderClass:
    """ Simple class to represent current calculated value (at start it is record itself), in operation list
    """
    inst = None

    def __new__(cls):
        if cls.inst is None:
            cls.inst = cls()
        return cls.inst

    def __str__(self):
        return "PlaceHolder"


PlaceHolder = PlaceHolderClass()


class Operator(object):
    """ Simple operator implementation for SField

        This class is used internaly to bound operations to SField class

        By default on init operation name is used to get
        corresponding implementation function from ``operator`` module

        :param str operation: name of operation, if no 'operation_fn' passed, then
                              operation function will be taken from `operator` module.
        :param callable operation_fn: function that implements operation
    """
    def __init__(self, operation, operation_fn=None):
        self.operation = operation

        # Get operation implementation
        if operation_fn is None:
            self.operation_fn = getattr(operator, self.operation)
        else:
            self.operation_fn = operation_fn

        self.__doc__ = self.operation_fn.__doc__
        self.__name__ = self.operation_fn.__name__

    def __call__(self, obj, *args):
        return obj.__add_op__(self.operation_fn,
                              [PlaceHolder] + list(args))

    def __get__(self, instance, cls):
        if instance is None:
            return six.create_unbound_method(self, cls)
        else:
            return six.create_bound_method(self, instance)


class SFieldMeta(type):
    """ SField's metaclass. At this time, just generates operator-related methods of SFields
    """

    def __new__(mcs, name, bases, attrs):
        cls = super(SFieldMeta, mcs).__new__(mcs, name, bases, attrs)

        for operation in SUPPORTED_OPERATIONS:
            sfield_operation = Operator(operation)
            setattr(cls, operation, sfield_operation)

        # Extra operator definition
        setattr(cls, '__getattr__', Operator('__getattr__', getattr))
        setattr(cls, '__call__', Operator('__call__', lambda x, *args: x(*args)))

        return cls


class SField(six.with_metaclass(SFieldMeta, object)):
    """ Class that allows to build simple expressions.
        For example, instead of writing something like::

            l = [{'a': 1, 'b': {'c': 5}, 'd': 4},
                 {'a': 2, 'b': {'c': 15}, 'd': 3}]
            l.sort(lambda x: x['a'] + x['b']['c'] - x['d'])

        With this class it is possible to write folowing::

            l = [{'a': 1, 'b': {'c': 5}, 'd': 4},
                 {'a': 2, 'b': {'c': 15}, 'd': 3}]
            SF = SField(dummy=True)
            l.sort((SF['a'] + SF['b']['c'] - SF['d'])._F)

        Or using SF shortcut and F wrapper defined in this module::

            from anyfield import SField, F
            l = [{'a': 1, 'b': {'c': 5}, 'd': 4},
                 {'a': 2, 'b': {'c': 15}, 'd': 3}]
            l.sort((SF['a'] + SF['b']['c'] - SF['d'])._F)

        :param bool dummy: if set to True, on next operation new SField instance will be created

    """

    def __init__(self, dummy=False):
        self._stack = []  # operation stack
        self._dummy = dummy

    def __add_op__(self, op, args):
        """ Add operation to operation stack of this SField instance

            :param callable op: callable that implements operation
            :param tuple args: arguments template for operation.
            :return: self
            :rtype: SField
        """
        obj = self if self._dummy is False else self.__class__(dummy=False)
        obj._stack.append((op, args))
        return obj

    def __calculate__(self, record):
        """ Do final calculation of this SField instances for specified record
        """
        res = record

        def process_args(args):
            """ Simple function to precess arguments
            """
            for arg in args:
                if arg is PlaceHolder:
                    yield res
                elif isinstance(arg, SField):
                    yield arg.__calculate__(record)
                else:
                    yield arg

        # TODO: implement keyword args processing

        for op, args in self._stack:
            args = tuple(process_args(args))
            res = op(*args)
        return res

    def _F(self, record):
        """ Shortcut for __calculate__ method

            If you need callable of one arg ot be passed for example to `filter` function
            Just finishe your expression with `._F` and You will get it
        """
        return self.__calculate__(record)


SF = SField(dummy=True)   # Shortcut
F = SField(dummy=True)


def toFn(fn):
    """ Simple wrapper to adapt SField instances to callables,
        that usualy used in .filter(), .sort() and other methods.

        If some part of Your code may accept SField instances or
        callable of one arg as parametrs, use this function to adapt argument
        for example::

            def my_super_filter_func(my_sequence, filter_fn):
                filter_fn = toFn(filter_fn)
                # Do your code

        This little line of code makes your function be able
        to use SField instances as filter_fn filter functions.

        :param fn: callable or SField instance
        :rtype: callable
        :return: if fn is instance of SField, thant it's method .__claculate__ will be returned,
                 otherwise 'fn' will be returned unchanged
    """
    if isinstance(fn, SField):
        return fn.__calculate__
    return fn
