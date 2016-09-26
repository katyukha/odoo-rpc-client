"""
"""

import six
from ..orm.object import Object


class ObjectUtils(Object):

    def convert_to_write(self, data):
        """ Simple function that adapts data, to be suitable
            for odoo write functions.

            At this moment used mostly to adapt results of
            odoo's ``onchange`` model method.

            :param dict data: data to be converted
            :return: data suitable for Odoo's create/write methods
        """
        def convert_many2one(field, value):
            """ Convert many2one field value.

                if value is tuple(id, name) return just id
            """
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return value[0]
            return value

        def convert_x2many(field, value):
            """ Convert many2many or one2many value

                many2many field value is just list of following commands::

                    (0, 0,  { fields })    create
                    (1, ID, { fields })    update (write fields to ID)
                    (2, ID)                remove (calls unlink on ID,
                                           that will also delete
                                           the relationship
                                           because of the ondelete)
                    (3, ID)                unlink (delete the relationship
                                           between the two objects but
                                           does not delete ID)
                    (4, ID)                link (add a relationship)
                    (5, ID)                unlink all
                    (6, ?, ids)            set a list of links
            """
            if not value:
                return False
            comodel = self.client[self.columns_info[field]['relation']]
            t_res = []
            for command in value:
                if command[0] in (0, 1):
                    t_res.append(
                        (command[0],
                         command[1],
                         comodel.convert_to_write(command[2]))
                    )
                else:
                    t_res.append(command)
            return t_res

        converters = {
            'many2one': convert_many2one,
            'many2many': convert_x2many,
            'one2many': convert_x2many,
        }

        res = {}
        for field, value in data.items():
            ftype = self.columns_info[field]['type']
            if ftype in converters:
                res[field] = converters[ftype](field, value)
            else:
                res[field] = value
        return res

    def get_view_info(self, view_id=None):
        """ Get view_info for specified model (result of ``fields_view_get``)

            if view_id is not passed, default model view is used
            if view_id is string, than it is assumed that it is xmlid of view

            :param str model: string model name (Ex. 'account.invoice')
            :param int|str view_id: integer ID or xmlid of view to get info for
            :return: result of model's ``fields_view_get``
        """
        if view_id is None:
            view_id = False  # xml-rpc cannot pass None(

        # if view_id is string then assume that it is xmlid of view
        if view_id and isinstance(view_id, six.string_types):
            view = self.client.external_ids.get_record(view_id)
            if (view and view._object.name == 'ir.ui.view'
                    and view.model == self.name):
                view_id = view.id
            else:
                raise Exception(
                    "Bad view_id: %s. found view: %s" % (view_id, view))

        return self.fields_view_get(view_id, 'form')
