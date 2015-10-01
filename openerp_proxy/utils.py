# -*- encoding: utf-8 -*-
import os
import six
import json
import functools

__all__ = ('ustr', 'AttrDict', 'wpartial')

# Python 2/3 workaround in raw_input
try:
    xinput = raw_input
except NameError:
    xinput = input


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
        and write only if conversion is successfule. This allows to avoid loss of data
        when rewriting file.
    """
    # note, using dumps instead of dump, becouse we need to check if data will
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


class UConverter(object):
    """ Simple converter to unicode

        Create instance with specified list of encodings to
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
                return six.text_type(value)
            except Exception:
                raise UnicodeError('unable to convert to unicode %r' % (value,))

        # value is binary type (str for python2 and bytes for python3)
        for ln in self.encodings:
            try:
                return six.text_type(value, ln)
            except Exception:
                pass
        raise UnicodeError('unable to convert %r' % (value,))

# default converter instance
ustr = UConverter()


if six.PY3:
    # There are no need to implement any aditional logic for Python 3, becuase
    # there base class 'object' already have implemented '__dir__' method,
    # which could be accessed via super() by subclasses
    class DirMixIn:
        pass
else:
    # implement basic __dir__ to make it assessible via super() by subclasses
    class DirMixIn(object):
        """ Mix in to make implementing __dir__ method in subclasses simpler
        """
        def __dir__(self):
            # code is based on
            # http://www.quora.com/How-dir-is-implemented-Is-there-any-PEP-related-to-that
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
        return super(AttrDict, self).__dir__() + self.keys()

