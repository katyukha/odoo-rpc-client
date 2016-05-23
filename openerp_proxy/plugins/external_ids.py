"""
"""

from ..plugin import Plugin
from ..orm.record import (Record,
                          RecordList)

import six


class ExternalIDS(Plugin):
    """ This plugin adds aditional methods to work with
        external_ids (xml_id) for Odoo records.
    """
    class Meta:
        name = "external_ids"

    def get_for(self, val, module=None):
        """ Return RecordList of 'ir.model.data' for val or False

            :param val: value to get 'ir.model.data' records for
            :param str module: module name to search 'ir.model.data' for
            :rtype: RecordList
            :return: RecordList with 'ir.model.data' records found
            :raises ValueError: if *val* argument could not be parsed

            ``val`` could be one of folowing types:

            - ``Record`` instance
            - ``RecordList`` instance
            - ``tuple(model, res_id)``, for example ``('res.partner', 5)``
            - ``str``, string in format 'module.name'.

            **Note**, in case of *val* is *str*: if *module*
            specified as parameter, then *val* supposed to be *name* only.
            For example, folowing calls are equal::

                cl.plugins.external_ids.get_for('base.group_configuration')
                cl.plugins.external_ids.get_for('group_configuration',
                                                module='base')
        """
        data_obj = self.client['ir.model.data']
        domain = [] if module is None else [('module', '=', module)]
        if isinstance(val, Record):
            domain += [('model', '=', val._object.name),
                       ('res_id', '=', val.id)]
        elif isinstance(val, RecordList):
            domain += [('model', '=', val._object.name),
                       ('res_id', 'in', val.ids)]
        elif isinstance(val, (tuple, list)) and len(val) == 2:
            model, res_id = val
            domain += [('model', '=', model),
                       ('res_id', '=', res_id)]
        elif isinstance(val, six.string_types):
            if module is None:
                try:
                    module, name = val.split('.')
                except ValueError:
                    raise ValueError(
                        "Bad xml_id passed. cannot fetch module name.")
            else:
                name = val

            domain = [('module', '=', module),
                      ('name', '=', name)]
        else:
            raise ValueError("Cannot parse value [%r]" % val)

        return data_obj.search_records(domain)

    def get_xmlid(self, val, module=None):
        """ Return *xml_id* for *val*.
            Note, that only first xml_id will be returned!

            :param val: look in documentation for
                `get_for
                <#openerp_proxy.plugins.external_ids.ExternalIDS.get_for>`__
                method
            :param str module: module name to search xml_id for
            :rtype: str
            :return: xml_id for *val* or False if not found
            :raises ValueError: if *val* argument could not be parsed

            Note, that if *module* specified as parametr, then *val*
            supposed to be *name* only
        """
        e_record = self.get_for(val, module=module)
        if e_record:
            return e_record[0].complete_name
        return False

    def get_record(self, xml_id, module=None):
        """ Return *Record* instance for specified xml_id

            :param str xml_id: string with xml_id to search record for
            :param str module: module name to search Record in
            :rtype: Record
            :return: Record for *val* or False if not found
            :raises ValueError: if *xml_id* argument could not be parsed
        """
        assert isinstance(xml_id, six.string_types), "xml_id must be string"
        e_record = self.get_for(xml_id, module=module)
        if e_record:
            e_record = e_record[0]
            return self.client[e_record.model].browse(e_record.res_id)
        return False


class Record__XMLIDS(Record):
    """ Simple class to add ability to get xmlid from record itself
    """
    def as_xmlid(self, module=None):
        """ Get xmlid for record

            :param str module: module to search xmlid in
            :return: xmlid for this record or False
            :rtype: str
        """
        return self._client.plugins.external_ids.get_xmlid(self, module=module)
