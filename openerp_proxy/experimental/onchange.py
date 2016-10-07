""" Implement onchange related logic for Odoo 8.0+ onchanges api
"""
try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
        except ImportError:
            raise

from .utils import ObjectUtils


class ObjectOnchangeUtils(ObjectUtils):

    def find_onchanges(self, view_info=None):
        """ Find onchange spec for specified model and view

            :param dict view_info: result of model's ``fields_view_get``
                                or ``get_view_info`` method
            :return: dict of format {'field': bool(have onchange)}
        """
        result = {}

        # for traversing the XML arch and populating result
        def process(node, info, prefix):
            if node.tag == 'field':
                name = node.attrib['name']
                names = "%s.%s" % (prefix, name) if prefix else name
                if not result.get(names):
                    result[names] = node.attrib.get('on_change', False)
                # traverse the subviews included in relational fields
                for subinfo in info['fields'][name].get('views', {}).values():
                    process(etree.fromstring(subinfo['arch']), subinfo, names)
            else:
                for child in node:
                    process(child, info, prefix)

        if view_info is None:
            view_info = self.get_view_info()
        process(etree.fromstring(view_info['arch']), view_info, '')
        return result

    def process_onchanges(self, data, fields=None,
                          view_info=None, context=None):
        """ Run onchanges

            :param dict data: data to be processed by onchanges
            :param list fields: list of changed fields (*optional*)
            :param dict view_info: result of model's ``fields_view_get``
                                   or ``get_view_info`` method (*optional*)
            :param dict context: context to prcess onchanges
                                 within (*optional*)
            :return: result of onchange events
        """
        res = self.onchange([],
                            data,
                            fields if fields is not None else [],
                            self.find_onchanges(view_info),
                            context=context)
        if res.get('warning', False):
            print('Warings %s' % res.get('warning', {}))
        return res.get('value', {})

    def process_onchanges_x(self, data, *args, **kwargs):
        """ Same as *process_onchanges* but applies *convert_to_write*
            method to its result
        """
        res = self.process_onchanges(data, *args, **kwargs)
        return self.convert_to_write(res)

    def parse_model_subfields(self, fields):
        """ returns tuple:
                tuple({model: [fields]}, model_fields, related_fields)
        """
        import collections
        sub_fields = collections.defaultdict(list)  # model: field
        r_fields = []   # related fields
        m_fields = []   # fields for current model
        for field in fields:
            if '.' in field:
                xfield, sub_field = field.split('.', 1)
                if xfield not in self.columns_info:
                    continue
                sub_field_rel = self.columns_info[xfield]['relation']
                sub_fields[sub_field_rel].append(sub_field)
                r_fields.append(xfield)
            else:
                m_fields.append(field)
        return sub_fields, m_fields, r_fields

    def process_onchanges_r(self, data, fields=None, view_info=None,
                            keep_fields=None, context=None):
        if view_info is None:
            view_info = self.get_view_info()

        fields = [] if fields is None else fields
        keep_fields = [] if keep_fields is None else keep_fields

        # parse fields
        sub_fields, m_fields, r_fields = self.parse_model_subfields(fields)

        # parse keep fields
        k_sub_fields, k_m_fields, k_r_fields = \
            self.parse_model_subfields(keep_fields)

        # run onchanges for current model
        res = self.process_onchanges_x(data,
                                       fields=m_fields,
                                       view_info=view_info,
                                       context=context)
        new_data = data.copy()
        new_data.update(res)

        # remove fields that should not be changed
        for k_field in k_m_fields:
            new_data[k_field] = data[k_field]

        for field in r_fields:
            value = new_data[field]
            field_info = self.columns_info[field]
            if field_info['type'] == 'one2many':
                comodel = self.client[field_info['relation']]
                comodel_field = field_info['relation_field']
                t_res = []
                for command in value:
                    if command[0] == 0:  # data not written to database
                        codata = command[2]  # command data
                        if not codata.get(comodel_field, False):
                            xdata = new_data.copy()     # result

                            # remove current field to avoid recursion
                            del xdata[field]

                            zdata = codata.copy()       # copy command data

                            # add data to field that point to parent record
                            zdata[comodel_field] = xdata

                            z_views = view_info['fields'][field]['views']
                            z_view_info = z_views.get('form',
                                                      z_views.get('tree',
                                                                  None))
                            z_res = comodel.process_onchanges_r(
                                zdata,
                                fields=sub_fields.get(comodel.name, []),
                                keep_fields=k_sub_fields.get(comodel.name, []),
                                view_info=z_view_info,
                                context=context)

                            del z_res[comodel_field]
                            codata.update(z_res)
                    t_res.append(command)
                new_data[field] = t_res

        if r_fields:
            new_data = self.process_onchanges_r(new_data,
                                                fields=r_fields,
                                                view_info=view_info,
                                                keep_fields=k_r_fields,
                                                context=context)

        return new_data
