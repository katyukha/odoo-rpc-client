""" Just imports of all extensions

    Importing this module, will automaticaly enable folowing extensions:
        - field_datetime  - Automaticaly convert 'date / time' fields to
                            ``datetime`` objects, thus allowing to compare
                            them in python
        - sugar           - Extra syntax sugar. Make code require less typing
        - workflow        - Odoo workflows related functionality
        - repr            - Rich representation of objects.
                            `IPython <http://ipython.org/>`__ /
                            `Jupyter <https://jupyter.org/>`__
                            integration layer

    Folowing names could be imported from this module:
        - ``HField``
        - ``HTMLTable``
        - ``FieldNotFoundException``

"""

from . import field_datetime  # noqa
from . import sugar           # noqa
from . import workflow        # noqa

from .repr import (FieldNotFoundException,  # noqa
                   HField,                  # noqa
                   HTMLTable)

__all__ = ('FieldNotFoundException',
           'HField',
           'HTMLTable')
