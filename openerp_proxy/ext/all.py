""" Just imports of all extensions
"""

import openerp_proxy.ext.field_datetime
import openerp_proxy.ext.sugar
import openerp_proxy.ext.workflow

from openerp_proxy.ext.repr import (FieldNotFoundException,
                                    HField,
                                    HTMLTable)

__all__ = ('FieldNotFoundException',
           'HField',
           'HTMLTable')
