""" This module provides additional representation capabilities
for most of standard classes like *Record* or *RecordList*.

This allows them to be represented as HTML tables in Jupyter notebook,
or for example show RecordList data as table in IPython console.
"""

# TODO: rename to IPython or something like that

from ... import (Client,
                 Session)
from ...service.object import ObjectService

from ...utils import ustr as _

from .utils import describe_object_html
from .generic import (FieldNotFoundException,
                      HField,
                      toHField,
                      PrettyTable,
                      BaseTable,
                      HTMLTable)

# import submodules
from .orm import *      # noqa
from .reports import *  # noqa

__all__ = (
    'FieldNotFoundException',
    'HField',
    'toHField',
    'PrettyTable',
    'BaseTable',
    'HTMLTable',
)


class ClientRegistedObjects(list):
    """ Simple class make registered objects be displayed as HTML table
    """
    def __init__(self, service, *args, **kwargs):
        super(ClientRegistedObjects, self).__init__(*args, **kwargs)
        self._service = service
        self._html_table = None

    @property
    def html_table(self):
        if self._html_table is None:
            ids = self._service.execute('ir.model',
                                        'search',
                                        [('model', 'in', list(self))])
            read = self._service.execute('ir.model',
                                         'read',
                                         ids,
                                         ['name', 'model', 'info'])
            self._html_table = HTMLTable(read,
                                         (('name', 'Name'),
                                          ('model', 'System Name'),
                                          ('info', 'Description')),
                                         caption='Registered models',
                                         display_help=False)
        return self._html_table

    def _repr_html_(self):
        """ HTML representation for registered objects
        """
        return self.html_table.render()


class ObjectServiceHtmlMod(ObjectService):
    """ Simple class to add some HTML display features to ObjectService
    """
    def _get_registered_objects(self):
        res = super(ObjectServiceHtmlMod, self)._get_registered_objects()
        return ClientRegistedObjects(self, res)


class ClientHTML(Client):
    """ HTML modifications for Client class
    """

    def _repr_html_(self):
        """ Builds HTML representation for IPython
        """
        help_text = (
            u"To get list of registered objects for thist database<br/>"
            u"access <i>registered_objects</i> property:<br/>"
            u"&nbsp;<i>.registered_objects</i><br/>"
            u"To get Object instance just call <i>get_obj</i> method<br/>"
            u"&nbsp;<i>.get_obj(name)</i><br/>"
            u"where <i>name</i> is name of Object You want to get"
            u"<br/>or use get item syntax instead:</br>"
            u"&nbsp;<i>[name]</i>"
        )

        return describe_object_html({
            "Host": self.host,
            "Port": self.port,
            "Protocol": self.protocol,
            "Database": self.dbname,
            "login": self.username,
        }, caption=u"RPC Client", help=help_text)


class IPYSession(Session):
    def _repr_html_(self):
        """ Provides HTML representation of session (Used for IPython)
        """
        help_text = (
            u"To get connection just call<br/> <ul>"
            u"<li>session.<b>aliase</b></li>"
            u"<li>session[<b>index</b>]</li>"
            u"<li>session[<b>aliase</b>]</li> "
            u"<li>session[<b>url</b>]</li>"
            u"<li>session.get_db(<b>url</b>|<b>index</b>|<b>aliase</b>)</li>"
            u"</ul>"
        )

        return describe_object_html(
            ((self._index_url(url),
              url,
              u", ".join((_(al)
                          for al, aurl in self.aliases.items()
                          if aurl == url)))
             for url in self._databases.keys()),
            caption='Previous connections',
            help=help_text,
            headers=[u'DB Index', u'DB URL', u'DB Aliases'])
