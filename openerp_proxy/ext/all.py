""" Just imports of all extensions

    Importing this module, will automaticaly enable folowing extensions:
        - field_datetime  - Automaticaly convert 'date / time' fields to ``datetime`` objects, thus allowing to compare them in python
        - sugar           - Extra syntax sugar. Make code require less typing
        - workflow        - Odoo workflows related functionality
        - repr            - Rich representation of objects. `IPython <http://ipython.org/>`_ / `Jupyter <https://jupyter.org/>`_ integration layer

    Folowing names could be imported from this module:
        - ``HField``
        - ``HTMLTable``
        - ``FieldNotFoundException``

"""

from . import field_datetime
from . import sugar
from . import workflow

from .repr import (FieldNotFoundException,
                   HField,
                   HTMLTable)

__all__ = ('FieldNotFoundException',
           'HField',
           'HTMLTable')
