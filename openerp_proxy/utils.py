# -*- encoding: utf-8 -*-
import os
import six
import json
import functools

__all__ = ('ustr',
           'AttrDict',
           'DirMixIn',
           'UConverter',
           'wpartial',
           'makedirs',
           'json_read',
           'json_write',
           'xinput',
           )


# Python 2/3 workaround in raw_input
try:
    xinput = raw_input
except NameError:
    xinput = input

# Check if anyfield is installed
# and import function which converts SField instances to functions
try:
    from anyfield import toFn as normalizeSField
except ImportError:
    def normalizeSField(fn):
        return fn


def makedirs(path):
    """ os.makedirs wrapper. No errors raised if directory already exists

        :param str path: directory path to create
    """
    try:
        os.makedirs(path)
    except os.error:
        pass


def json_read(file_path):
    """ Read specified json file
    """
    with open(file_path, 'rt') as json_data:
        data = json.load(json_data)
    return data


def json_write(file_path, *args, **kwargs):
    """ Write data to specified json file

        Note, this function uses dumps function to convert data to json first,
        and write only if conversion is successfule. This allows to avoid
        loss of data when rewriting file.
    """
    # note, using dumps instead of dump, because we need to check if data will
    # be dumped correctly. using dump on incorect data, causes file to be half
    # written, and thus broken
    json_data = json.dumps(*args, **kwargs)

    with open(file_path, 'wt') as json_file:
        json_file.write(json_data)


def wpartial(func, *args, **kwargs):
    """Wrapped partial, same as functools.partial decorator,
       but also calls functools.wrap on its result thus shwing correct
       function name and representation.
    """
    partial = functools.partial(func, *args, **kwargs)

    return functools.wraps(func)(partial)


def preprocess_args(*args, **kwargs):
    """ Skip all args, and kwargs that set to None

        Mostly for internal usage.

        Used to workaround xmlrpc None restrictions
    """
    kwargs = {key: val for key, val in kwargs.items() if val is not None}

    xargs = list(args[:])
    while xargs and xargs[-1] is None:
        xargs.pop()
    return xargs, kwargs


def stdcall(fn):
    """ Simple decorator for server methods, that supports standard call

        If method supports call like
        ``method(ids, <args>, context=context, <kwargs>)``,
        then it may be decrated by this decorator to appear in
        dir(record) and dir(recordlist) calls, thus making it available
        for autocompletition in ipython or other python shells
    """
    fn.__x_stdcall__ = True
    return fn


class UConverter(object):
    """ Simple converter to unicode

        Create instance with specified list of encodings to be used to
        try to convert value to unicode

        Example::

            ustr = UConverter(['utf-8', 'cp-1251'])
            my_unicode_str = ustr(b'hello - привет')
    """
    default_encodings = ['utf-8', 'ascii']

    def __init__(self, hint_encodings=None):
        if hint_encodings:
            self.encodings = hint_encodings
        else:
            self.encodings = self.default_encodings[:]

    def __call__(self, value):
        """ Convert value to unicode

        :param value: the value to convert
        :raise: UnicodeError if value cannot be coerced to unicode
        :return: unicode string representing the given value
        """
        # it is unicode
        if isinstance(value, six.text_type):
            return value

        # it is not binary type (str for python2 and bytes for python3)
        if not isinstance(value, six.binary_type):
            try:
                value = six.text_type(value)
            except Exception:
                # Cannot directly convert to unicode. So let's try to convert
                # to binary, and that try diferent encoding to it
                try:
                    value = six.binary_type(value)
                except:
                    raise UnicodeError('unable to convert to unicode %r'
                                       '' % (value,))
            else:
                return value

        # value is binary type (str for python2 and bytes for python3)
        for ln in self.encodings:
            try:
                res = six.text_type(value, ln)
            except Exception:
                pass
            else:
                return res

        raise UnicodeError('unable to convert to unicode %r' % (value,))

# default converter instance
ustr = UConverter()


# DirMixIn class implementation. To be able to use super calls to __dir__ in
# subclasses (Py 2/3 support)
# code is based on
# http://www.quora.com/How-dir-is-implemented-Is-there-any-PEP-related-to-that
try:
    object.__dir__
except AttributeError:
    class DirMixIn(object):
        """ Mix-in to make implementing __dir__ method in subclasses simpler
        """
        def __dir__(self):
            def get_attrs(obj):
                import types
                if not hasattr(obj, '__dict__'):
                    return []  # slots only
                if not isinstance(obj.__dict__, (dict, types.DictProxyType)):
                    raise TypeError("%s.__dict__ is not a dictionary"
                                    "" % obj.__name__)
                return obj.__dict__.keys()

            def dir2(obj):
                attrs = set()
                if not hasattr(obj, '__bases__'):
                    # obj is an instance
                    if not hasattr(obj, '__class__'):
                        # slots
                        return sorted(get_attrs(obj))
                    klass = obj.__class__
                    attrs.update(get_attrs(klass))
                else:
                    # obj is a class
                    klass = obj

                for cls in klass.__bases__:
                    attrs.update(get_attrs(cls))
                    attrs.update(dir2(cls))
                attrs.update(get_attrs(obj))
                return list(attrs)

            return dir2(self)
else:
    # There are no need to implement any aditional logic for Python 3.3+,
    # because there base class 'object' already have implemented
    # '__dir__' method, which could be accessed via super() by subclasses
    class DirMixIn:
        pass


class AttrDict(dict, DirMixIn):
    """ Simple class to make dictionary able to use attribute get operation
        to get elements it contains using syntax like:

        >>> d = AttrDict(arg1=1, arg2='hello')
        >>> print(d.arg1)
            1
        >>> print(d.arg2)
            hello
        >>> print(d['arg2'])
            hello
        >>> print(d['arg1'])
            1
    """
    def __getattr__(self, name):
        res = None
        try:
            res = super(AttrDict, self).__getitem__(name)
        except KeyError as e:
            raise AttributeError(str(e))
        return res

    def __dir__(self):
        res = super(AttrDict, self).__dir__() + list(self.keys())
        return list(set(res))
