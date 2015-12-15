"""
"""

import six

from .utils import ustr as _

import operator

__all__ = ('SField', 'SF', 'PlaceHolder')

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
    """
    def __init__(self, operation):
        self.operation = operation
        self.operation_fn = getattr(operator, self.operation)
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

        return cls


class SField(six.with_metaclass(SFieldMeta, object)):
    """

       Examples:

           from openerp_proxy.anyfield import SField, SF

           fn = (SField()[5] + 4) < (SField()['my-field'] + 5)

           fn += SField() + 6

           fn -= SF -5


       :param bool dummy: if set to True, on next operation new SField instance will be created

    """

    def __init__(self, dummy=False):
        self._stack = []  # operation stack
        self._dummy = dummy

    def __add_op__(self, op, args):
        obj = self if self._dummy is False else self.__class__(dummy=False)
        obj._stack.append((op, args))
        return obj

    def __calculate__(self, record):
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

    # TODO: think, is it right, or it would be better to make this method
    # similary to other operators to be applied on record?
    def __call__(self, record):
        return self.__calculate__(record)


SF = SField(dummy=True)   # Shortcut
F = SField(dummy=True)    # Shortcut
