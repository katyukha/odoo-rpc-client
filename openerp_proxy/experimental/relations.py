"""
This module contains functions and classes that could be used to get
information abour record relations
"""

from ..ext import sugar  # noqa
from ..orm.object import Object
from ..orm.record import (Record, RecordList)


class RelationsObject(Object):

    def get_related_models(self, cache=None):
        """ Get related models for specified model

            return RecordList('ir.model') which contains models related to
            specified model
        """
        if cache is None:
            cache = {}

        cache_key = 'related-models-for-%s-%s' % (id(self), self.name)
        related_models = cache.get(cache_key, None)
        if related_models is None:
            related_models = self.client._ir_model_fields(
                [('relation', '=', self.name)]).mapped('model_id')
            cache[cache_key] = related_models

        return related_models

    def get_related_model_fields(self, cache=None):
        """ Get a dictionary {<model>: RecordList('ir.model.fields')}
            which contains related models, and list of relational fields
            that points to specified model
        """
        if cache is None:
            cache = {}

        cache_key = 'related-model-fields-for-%s-%s' % (id(self), self.name)

        related_models = self.get_related_models(cache)
        related_model_fields = cache.get(cache_key, None)
        if related_model_fields is None:
            related_model_fields = {
                model: model.field_id.filter(lambda x: x.relation == self.name)
                for model in related_models
            }
            cache[cache_key] = related_model_fields
        return related_model_fields


class RecordRelations(Record):

    def get_rel_data_domain(self, field):
        if field.ttype == 'many2one':
            return [(field.name, '=', self.id)]
        elif field.ttype in ('one2many', 'many2many'):
            return [(field.name, 'in', [self.id])]
        else:
            return []

    def find_related_objects(self, skip_models=None, cache=None):
        """ Find all links to this record
        """
        cl = self._object.client
        skip_models = [] if skip_models is None else skip_models

        if cache is None:
            cache = {}

        # import pudb; pudb.set_trace()  # XXX BREAKPOINT
        related_model_fields = self._object.get_related_model_fields(cache)

        model_fields = {}
        for model in related_model_fields:
            if model.model in skip_models:
                continue
            model_fields_data = {}
            model_cl = cl[model.model]
            for field in related_model_fields[model]:
                rel_data_domain = self.get_rel_data_domain(field)
                if model_cl.search(rel_data_domain, count=1):
                    model_fields_data[field.name] = model_cl.search_records(
                        rel_data_domain)

            if model_fields_data:
                model_fields[model.model] = model_fields_data

        return model_fields


class RecordListRelations(RecordList):

    def find_related_objects_multi(self, skip_models, cache=None):
        """ Find all links to all records from other models
        """
        cl = self.object.client
        model = self.object.name
        skip_models = [] if skip_models is None else skip_models

        if cache is None:
            cache = {}

        related_model_fields = self.object.get_related_model_fields(cache)

        model_fields_to_check = {
            model: [
                field for field in fields
                if cl[model.model].search([(field.name, 'in', self.ids)],
                                          count=1)
            ]
            for model, fields in related_model_fields.items()
            if model.model not in skip_models
        }

        model_fields_to_check = {
            model: fields
            for model, fields in model_fields_to_check.items()
            if fields
        }

        res = {
            # <record>: {<model>: {<field>: <related_records}}
        }

        for record in self:
            record_data = {}   # {<model>: {<field>: <related_records}}
            for model, fields in model_fields_to_check.items():
                record_model_data = {}  # {<field>: <related_records}
                for field in fields:
                    field_data = cl[model.model](
                        record.get_rel_data_domain(field))

                    if field_data:
                        record_model_data[field] = field_data

                if record_model_data:
                    record_data[model] = record_model_data

            if record_data:
                res[record] = record_data

        return res
