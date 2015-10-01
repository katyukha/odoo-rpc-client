# -*- coding: utf-8 -*-
from extend_me import Extensible

from ..plugin import Plugin
from ..orm.object import Object

try:
    import pydot
except ImportError:
    print("PyDot not installed!!!")


class Model(Extensible):
    """ Class that represents model in pydot.Graph
    """

    def __init__(self, proxy, obj):
        self._proxy = proxy
        self._object = obj if isinstance(obj, Object) else self._proxy[obj]

    def __eq__(self, other):
        return self._object == other._object

    @property
    def name(self):
        return self._object.name

    @property
    def object(self):
        return self._object

    @property
    def fields_info(self):
        return self._object.columns_info

    def get_extra_node_args(self):
        return {
            'margin': '0',
            'shape': 'record',
            'label': self._object.model_name
        }

    def to_node(self):
        """ Create pydot.Node instance for this relation
        """
        return pydot.Node(self._object.name,
                          **self.get_extra_node_args())

    def add_to_graph(self, graph):
        """ Add this model to graph
        """
        graph.add_node(self.to_node())


class ModelRelation(Extensible):
    """ Class that represents Relation in pydot graph
    """
    def __init__(self, proxy, model, field_name, field_data):
        assert isinstance(model, Model)
        self._proxy = proxy
        self._model = model
        self._field_name = field_name
        self._field_data = field_data
        assert field_data['type'] in ('many2many', 'many2one'), "Wrong type: %s:%s" % (field_name, field_data['type'])

        self._related_model = None

    @property
    def proxy(self):
        """ Related Client instance
        """
        return self._proxy

    @property
    def field_name(self):
        """ Name of field of model, this relation is binded to
        """
        return self._field_name

    @property
    def field_data(self):
        """ Field info, got from fields_get method
        """
        return self._field_data

    @property
    def type(self):
        """ Relation type. One of ('many2one', 'many2many')
        """
        return self.field_data['type']

    @property
    def model(self):
        """ Model instance this relation is binded to
        """
        return self._model

    @property
    def object(self):
        """ Object this relation is binded to
        """
        return self.model.object

    @property
    def related_object(self):
        """ Related object
        """
        return self.proxy[self.field_data['relation']]

    @property
    def related_model(self):
        """ Related model
        """
        if self._related_model is None:
            self._related_model = Model(self.proxy, self.related_object)
        return self._related_model

    @property
    def m2m_join_table(self):
        """ If possible get join table for m2m relation. otherwise return False
        """
        return self.field_data.get('m2m_join_table', False)

    @property
    def m2m_join_columns(self):
        """ If possible get join columns for m2m relation. otherwise return False
        """
        return self.field_data.get('m2m_join_columns', False)

    def __eq__(self, other):
        if self.proxy != other.proxy:
            return False

        if self.model.name == other.model.name and self.field_name == other.field_name:
            return True

        if self.type != other.type:
            return False

        if self.related_model.name != other.model.name or self.model.name != other.related_model.name:
            return False

        # note, both objects have same type here
        if self.type == 'many2many':
            return (self.m2m_join_table and other.m2m_join_table and
                    self.m2m_join_columns and other.m2m_join_columns and
                    self.m2m_join_table == other.m2m_join_table and
                    self.m2m_join_columns == reversed(other.m2m_join_columns))

        return False

    def get_extra_edge_args(self):
        return {
            'label': self.field_name,
            'labeldistance': '10.0'
        }

    def to_edge(self):
        """ Create pydot.Edge instance for this relation
        """
        return pydot.Edge(self.model.name,
                          self.related_model.name,
                          **self.get_extra_edge_args())

    def add_to_graph(self, graph):
        """ Add this relation to graph
        """
        graph.add_edge(self.to_edge())


class ModelGraph(Extensible):
    """ Contains single model graph
    """

    def __init__(self, proxy, models, depth=1):
        """
            :param models: list of Object instances of models to build graph for
        """
        self._proxy = proxy
        self._depth = depth
        self._models = [Model(proxy, m) for m in models]

        self._relations = []
        self._processed_models = []

        self._graph = None

    @property
    def depth(self):
        """ Graph depth
        """
        return self._depth

    @property
    def graph(self):
        """ Return pydot.Dot instance of graph
        """
        if self._graph is None:
            return self.generate_graph()
        return self._graph

    def clean(self):
        """ Clean graph
        """
        self._graph = None
        self._relations = []
        self._processed_models = []

    def _find_relations(self, model=None, level=0):
        """ Finds relation between selected models
        """
        if model is None:
            for model in self._models:
                self._find_relations(model)
        else:
            self._processed_models.append(model)
            for field_name, field in model.fields_info.iteritems():
                if field['type'] in ('many2one', 'many2many'):
                    relation = ModelRelation(self._proxy, model, field_name, field)
                elif field['type'] == 'one2many':
                    rel_model = Model(self._proxy, field['relation'])
                    rel_field = field['relation_field']
                    rel_field_data = rel_model.fields_info[rel_field]
                    if rel_field_data['type'] != 'many2one':
                        # skip non-standard relations
                        continue
                    relation = ModelRelation(self._proxy, rel_model, rel_field, rel_field_data)
                else:
                    continue

                if relation not in self._relations:
                    self._relations.append(relation)
                    self._processed_models.append(relation.related_model)
                    related = relation.related_model
                    if level < self._depth and related not in self._processed_models:
                        self._find_relations(related, level + 1)
        return self._processed_models, self._relations

    def generate_graph(self):
        """ Return pydot.Dot instance of graph
        """
        self._graph = pydot.Dot(graph_type='digraph', overlap='scalexy', splines='true')

        models, relations = self._find_relations()

        for model in models:
            # todo add nodes
            model.add_to_graph(self._graph)

        for relation in relations:
            if relation.model not in models:
                relation.model.add_to_graph(self._graph)
            if relation.related_model not in models:
                relation.related_model.add_to_graph(self._graph)
            relation.add_to_graph(self._graph)

        return self._graph


class Graph(Plugin):
    """ Plugin that allow to build graphs.

        At this point it is in experimental stage
    """

    class Meta:
        name = "graph"

    def __init__(self, *args, **kwargs):
        super(Graph, self).__init__(*args, **kwargs)

    def model_graph(self, models, depth=1):
        return ModelGraph(self.proxy, models, depth=depth)
