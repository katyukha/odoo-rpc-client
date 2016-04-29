from jinja2 import Template


TEMPLATE_BASE = Template("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<graphml
  xmlns="http://graphml.graphdrawing.org/xmlns"
  xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java"
  xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0"
  xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:y="http://www.yworks.com/xml/graphml"
  xmlns:yed="http://www.yworks.com/xml/yed/3"
  xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">

    <!--Created by Openerp Proxy project-->
    <key for="port" id="d0" yfiles.type="portgraphics"/>
    <key for="port" id="d1" yfiles.type="portgeometry"/>
    <key for="port" id="d2" yfiles.type="portuserdata"/>
    <key attr.name="url" attr.type="string" for="node" id="d3"/>
    <key attr.name="description" attr.type="string" for="node" id="d4"/>
    <key for="node" id="d5" yfiles.type="nodegraphics"/>
    <key for="graphml" id="d6" yfiles.type="resources"/>
    <key attr.name="url" attr.type="string" for="edge" id="d7"/>
    <key attr.name="description" attr.type="string" for="edge" id="d8"/>
    <key for="edge" id="d9" yfiles.type="edgegraphics"/>

    <graph edgedefault="directed" id="G">
        {% for node in nodes %}
            {{ node.to_graphml() }}
        {% endfor %}
        {% for edge in edges %}
            {{ edge.to_graphml() }}
        {% endfor %}
    </graph>
    <data key="d6">
        <y:Resources/>
    </data>
</graphml>

""")  # noqa

TEMPLATE_NODE_BIG_ENTITY = Template("""
<node id="{{ node.id }}">
<data key="d4"/>
<data key="d5">
    <y:GenericNode configuration="com.yworks.entityRelationship.big_entity">
        <y:Geometry height="{{ node.height }}" width="{{ node.width }}"
                    x="0" y="0"/>
        <y:Fill color="#E8EEF7" color2="#B7C9E3" transparent="false"/>
        <y:BorderStyle color="#000000" type="line" width="1.0"/>
        <y:NodeLabel alignment="center" autoSizePolicy="content"
                     backgroundColor="#B7C9E3"
                     configuration="com.yworks.entityRelationship.label.name"
                     fontFamily="Dialog" fontSize="12" fontStyle="plain"
                     hasLineColor="false"
                     modelName="internal" modelPosition="t"
                     textColor="#000000" visible="true"
                     >{{ node.label }}</y:NodeLabel>
        <y:NodeLabel alignment="left" autoSizePolicy="content"
                     configuration="com.yworks.entityRelationship.label.attributes"
                     fontFamily="Dialog" fontSize="12" fontStyle="plain"
                     hasBackgroundColor="false"
                     hasLineColor="false"
                     modelName="custom" textColor="#000000"
                     visible="true">{{ node.attributes }}<y:LabelModel>
                <y:ErdAttributesNodeLabelModel/>
            </y:LabelModel>
            <y:ModelParameter>
                <y:ErdAttributesNodeLabelModelParameter/>
            </y:ModelParameter>
        </y:NodeLabel>
        <y:StyleProperties>
            <y:Property class="java.lang.Boolean"
                        name="y.view.ShadowNodePainter.SHADOW_PAINTING"
                        value="true"/>
        </y:StyleProperties>
    </y:GenericNode>
</data>
</node>
""")

TEMPLATE_NODE_RELATIONSHIP = Template("""
<node id="{{ node.id }}">
    <data key="d4"/>
    <data key="d5">
    <y:GenericNode configuration="com.yworks.entityRelationship.relationship">
        <y:Geometry height="{{ node.height }}" width="{{ node.width }}"
                    x="1" y="0"/>
        <y:Fill color="#E8EEF7" color2="#B7C9E3" transparent="false"/>
        <y:BorderStyle color="#000000" type="line" width="1.0"/>
        <y:NodeLabel alignment="center" autoSizePolicy="content"
                     fontFamily="Dialog"
                     fontSize="12" fontStyle="plain" hasBackgroundColor="false"
                     hasLineColor="false"
                     height="17.96875" width="78.203125"
                     modelName="custom" textColor="#000000"
                     visible="true" x="1" y="1">{{ node.label }}<y:LabelModel>
            <y:SmartNodeLabelModel distance="4.0"/>
        </y:LabelModel>
        <y:ModelParameter>
            <y:SmartNodeLabelModelParameter labelRatioX="0.0" labelRatioY="0.0"
                                            nodeRatioX="0.0" nodeRatioY="0.0"
                                            offsetX="0.0" offsetY="0.0"
                                            upX="0.0" upY="-1.0"/>
        </y:ModelParameter>
        </y:NodeLabel>
        <y:StyleProperties>
        <y:Property class="java.lang.Boolean"
                    name="y.view.ShadowNodePainter.SHADOW_PAINTING"
                    value="true"/>
        </y:StyleProperties>
    </y:GenericNode>
    </data>
</node>
""")

TEMPLATE_EDGE = Template("""
<edge id="{{ edge.id }}" source="{{ edge.source.id }}"
      target="{{ edge.target.id }}">
    <data key="d8"/>
    <data key="d9">
        <y:PolyLineEdge>
            <y:Path sx="0.0" sy="0.0" tx="0.0" ty="0.0"/>
            <y:LineStyle color="#000000" type="line" width="1.0"/>
            <y:Arrows source="{{ edge.source_arrow }}"
                      target="{{ edge.target_arrow }}"/>
            <y:EdgeLabel alignment="center"
                         configuration="AutoFlippingLabel"
                         distance="2.0" fontFamily="Dialog"
                         fontSize="12" fontStyle="plain"
                         hasBackgroundColor="false"
                         hasLineColor="false"
                         height="{{ edge.height }}" modelName="custom"
                         preferredPlacement="anywhere"
                         ratio="0.5" textColor="#000000" visible="true"
                         width="{{ edge.width }}"
                         x="0" y="0">{{ edge.label }}
                <y:LabelModel>
                    <y:SmartEdgeLabelModel autoRotationEnabled="false"
                                           defaultAngle="0.0"
                                           defaultDistance="10.0"/>
                </y:LabelModel>
                <y:ModelParameter>
                    <y:SmartEdgeLabelModelParameter angle="0.0"
                                                    distance="30.0"
                                                    distanceToCenter="true"
                                                    position="right"
                                                    ratio="0.5"
                                                    segment="0"/>
                </y:ModelParameter>
                <y:PreferredPlacementDescriptor angle="0.0"
                                                angleOffsetOnRightSide="0"
                                                angleReference="absolute"
                                                angleRotationOnRightSide="co"
                                                distance="-1.0" frozen="true"
                                                placement="anywhere"
                                                side="anywhere"
                                                sideReference="relative_to_edge_flow"/>
            </y:EdgeLabel>
            <y:BendStyle smoothed="false"/>
        </y:PolyLineEdge>
    </data>
</edge>
""")


ALLOWED_EDGE_ARROW_STYLES = ['crows_foot_one', 'crows_foot_many', 'none']


# Constants
CHAR_WIDTH = 7.0
LINE_HEIGHT = 15.0


class Node(object):
    __last_id = 0

    # should be overridden in subclasses
    _template = None
    _id_prefix = 'node_id_'

    line_width_mod = CHAR_WIDTH
    line_height_mod = LINE_HEIGHT

    @classmethod
    def get_id(cls):
        cls.__last_id += 1
        return "{id_prefix}{id}".format(
            id_prefix=cls._id_prefix,
            id=cls.__last_id)

    def __init__(self, label):
        self.label = str(label)
        self.id = self.get_id()

    @property
    def width(self):
        lines = (self.label + '\n').split('\n')
        return max((len(line) for line in lines)) * \
            self.line_width_mod + self.line_width_mod

    @property
    def height(self):
        return (1.0 + self.label.count('\n')) * \
            self.line_height_mod + self.line_height_mod

    def to_graphml(self):
        if self._template is None:
            raise NotImplemented("There is no defined template for this class")
        return self._template.render(node=self)

    def __str__(self):
        return "<%s: %s>" % (self.id, self.label)

    def __repr__(self):
        return str(self)


class NodeRelationship(Node):
    _template = TEMPLATE_NODE_RELATIONSHIP
    _id_prefix = 'node_relationship_'

    line_width_mod = CHAR_WIDTH + 1
    line_height_mod = LINE_HEIGHT + 1


class NodeBigEntity(Node):

    _template = TEMPLATE_NODE_BIG_ENTITY
    _id_prefix = 'node_entity_big_'

    def __init__(self, label, attributes):
        self.attributes = str(attributes)
        super(NodeBigEntity, self).__init__(label)

    @property
    def width(self):
        lines = (self.label + '\n' + self.attributes).split('\n')
        return max((len(line)
                   for line in lines)) * CHAR_WIDTH + self.line_width_mod

    @property
    def height(self):
        return ((1.0 + self.label.count('\n') + 1.0 +
                 self.attributes.count('\n')) * LINE_HEIGHT +
                self.line_height_mod)


class Edge(object):
    __last_id = 0

    _template = TEMPLATE_EDGE
    _id_prefix = 'edge_id_'

    @classmethod
    def get_id(cls):
        cls.__last_id += 1
        return "{id_prefix}{id}".format(
            id_prefix=cls._id_prefix,
            id=cls.__last_id)

    def __init__(
            self,
            source,
            target,
            label='',
            source_arrow='none',
            target_arrow='none'):
        self.source = source
        self.target = target
        self.label = label
        self.source_arrow = source_arrow
        self.target_arrow = target_arrow
        self.id = self.get_id()

    @property
    def width(self):
        lines = self.label.split('\n')
        return max((len(line) for line in lines)) * CHAR_WIDTH

    @property
    def height(self):
        return (1.0 + self.label.count('\n')) * LINE_HEIGHT + LINE_HEIGHT / 2

    def to_graphml(self):
        return self._template.render(edge=self)

    def __str__(self):
        return "<%s: %s -> %s (%s)>" % (self.id,
                                        self.source,
                                        self.target,
                                        self.label)

    def __repr__(self):
        return str(self)


class Graph(object):
    _template = TEMPLATE_BASE

    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def to_graphml(self):
        return self._template.render(nodes=self.nodes, edges=self.edges)

    def to_file(self, path):
        with open(path, 'wt') as f:
            f.write(self.to_graphml())
