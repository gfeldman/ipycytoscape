#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Mariana Meireles.
# Distributed under the terms of the Modified BSD License.

import copy

from spectate import mvc
from traitlets import TraitType

from ipywidgets import DOMWidget, Widget, widget_serialization
from traitlets import Unicode, Bool, CFloat, Integer, Instance, Dict, List, Union
from ._frontend import module_name, module_version

"""TODO: Remove this after this is somewhat done"""
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class Mutable(TraitType):
    """A base class for mutable traits using Spectate"""

    _model_type = None
    _event_type = "change"

    def instance_init(self, obj):
        default = self._model_type()

        @mvc.view(default)
        def callback(default, events):
            change = dict(
                new=getattr(obj, self.name),
                name=self.name,
                type=self._event_type,
            )
            obj.notify_change(change)

        setattr(obj, self.name, default)

class MutableDict(Mutable):
    """A mutable dictionary trait"""
    _model_type = mvc.Dict

class MutableList(Mutable):
    """A mutable list trait"""
    _model_type = mvc.List

class Edge(Widget):
    """ Edge Widget """
    _model_name = Unicode('EdgeModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    group = Unicode().tag(sync=True)
    removed = Bool().tag(sync=True)
    selected = Bool().tag(sync=True)
    selectable = Bool().tag(sync=True)
    locked = Bool().tag(sync=True)
    grabbed = Bool().tag(sync=True)
    grabbable = Bool().tag(sync=True)
    classes = Unicode().tag(sync=True)

    data = MutableDict().tag(sync=True)
    position = MutableDict().tag(sync=True)


class Node(Widget):
    """ Node Widget """
    _model_name = Unicode('NodeModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('NodeView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    group = Unicode().tag(sync=True)
    removed = Bool().tag(sync=True)
    selected = Bool().tag(sync=True)
    selectable = Bool().tag(sync=True)
    locked = Bool().tag(sync=True)
    grabbed = Bool().tag(sync=True)
    grabbable = Bool().tag(sync=True)
    classes = Unicode().tag(sync=True)

    data = MutableDict().tag(sync=True)
    position = MutableDict().tag(sync=True)


def _set_attributes(instance, data):
    cyto_attrs = ['group', 'removed', 'selected', 'selectable',
                    'locked', 'grabbed', 'grabbable', 'classes', 'position', 'data']
    for k, v in data.items():
        if k in cyto_attrs:
            setattr(instance, k, v)
        else:
            instance.data[k] = v

class Graph(Widget):
    """ Graph Widget """
    _model_name = Unicode('GraphModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    nodes = MutableList(Instance(Node)).tag(sync=True, **widget_serialization)
    edges = MutableList(Instance(Edge)).tag(sync=True, **widget_serialization)
    # dictionary for syncing graph structure
    _adj = dict()

    def add_node(self, node):
        """
        Appends node to the end of the list. Equivalent to Python's append method.
        Parameters
        ----------
        self: cytoscape graph
        node: cytoscape node
        """
        if node.data['id'] not in self._adj:
            self._adj[node.data['id']] = dict()
            self.nodes.append(node)

    def remove_node(self, node):
        """
        Removes node from the end of the list. Equivalent to Python's remove method.
        Parameters
        ----------
        self: cytoscape graph
        node: cytoscape node
        """
        try:
            self.nodes.remove(node)
            for target in list(self._adj[node.data['id']]):
                self.remove_edge_by_id(node.data['id'], target)
            for source in list(self._adj):
                for target in list(self._adj[source]):
                    if target == node.data['id']:
                        self.remove_edge_by_id(source, node.data['id'])
            del self._adj[node.data['id']]
        except ValueError:
            raise ValueError(f'{node.data["id"]} is not present in the graph.')

    def remove_node_by_id(self, node_id):
        """
        Removes node by the id specified.
        Parameters
        ----------
        self: cytoscape graph
        node_id: numeric types and string
        """
        node_list_id = -1
        for i, node in enumerate(self.nodes):
            if node.data['id'] == node_id:
                node_list_id = i
                # for target in self._adj[node_id]:
                #     self.remove_edge_by_id(node_id, target)
                # for source in self._adj:
                #     for target in source:
                #         if target == node_id:
                #             self.remove_edge_by_id(source, node_id)
                # del self._adj[node_id]
                # break
        if node_list_id != -1:
            self.remove_node(self.nodes[node_list_id])
        else:
            raise ValueError(f'{node.data["id"]} is not present in the graph.')

    def add_edge(self, edge, directed=False):
        """
        Appends edge from the end of the list. Equivalent to Python's append method.
        Parameters
        ----------
        self: cytoscape graph
        edge: cytoscape edge
        directed: boolean
        """
        source, target = edge.data['source'], edge.data['target']
        
        if (source in self._adj and target in self._adj[source]) or (not directed and target in self._adj and source in self._adj[target]):
            pass
        else: # if the edge is not present in the graph
            self.edges.append(edge)
            if source not in self._adj:
                node_instance = Node()
                # setting the id, according to current spec should be only int/str
                node_instance.data = {'id': source}
                self.add_node(node_instance)
            if target not in self._adj:
                node_instance = Node()
                # setting the id, according to current spec should be only int/str
                node_instance.data = {'id': target}
                self.add_node(node_instance)
            self._adj[source][target] = dict()
            if not directed:
                self._adj[target][source] = dict()

    def remove_edge(self, edge):
        """
        Removes edge from the end of the list.  Equivalent to Python's remove method.
        Parameters
        ----------
        self: cytoscape graph
        edge: cytoscape edge
        """
        try:
            self.edges.remove(edge)
            del self._adj[edge.data['source']][edge.data['target']]
            if not edge.classes == 'directed':
                 del self._adj[edge.data['target']][edge.data['source']]
        except ValueError:
            raise ValueError(f"Edge from {edge.data['source']} to {edge.data['target']} is not present in the graph.")

    def remove_edge_by_id(self, source_id, target_id):
        """
        Removes edge by the id specified.
        Parameters
        ----------
        self: cytoscape graph
        source_id: numeric types and string
        target_id: numeric types and string
        """
        edge_id = -1
        for i, edge in enumerate(self.edges):
            if edge.data['source'] == source_id and edge.data['target'] == target_id:
                edge_id = i
        
        if edge_id != -1:
            self.remove_edge(self.edges[edge_id])
        else:
            raise ValueError(f"Edge from {edge.data['source']} to {edge.data['target']} is not present in the graph.")

    def add_graph_from_networkx(self, g, directed=False):
        """
        Converts a NetworkX graph in to a Cytoscape graph.
        Parameters
        ----------
        self: cytoscape graph
        g: nx graph
            receives a generic NetworkX graph. more info in
            https://networkx.github.io/documentation/
        directed: boolean
            If true all edges will be given directed as class if
            they do not already have it. Equivalent to adding
            'directed' to the 'classes' attribute of edge.data for all edges
        """
        for node, data in g.nodes(data=True):
            node_instance = Node()
            _set_attributes(node_instance, data)
            if 'id' not in data:
                node_instance.data['id'] = node
            # self.nodes.append(node_instance)
            self.add_node(node_instance)

        for source, target, data in g.edges(data=True):
            edge_instance = Edge()
            edge_instance.data['source'] = source
            edge_instance.data['target'] = target
            _set_attributes(edge_instance, data)

            if directed and 'directed' not in edge_instance.classes:
                edge_instance.classes += ' directed '
            # self.edges.append(edge_instance)
            self.add_edge(edge_instance)

    def add_graph_from_json(self, json_file, directed=False):
        """
        Converts a JSON Cytoscape graph in to a ipycytoscape graph.
        (This method only allows the conversion from a JSON that's already
        formatted as a Cytoscape graph).
        Parameters
        ----------
        self: cytoscape graph
        json_file: json file
        directed: boolean
            If True all edges will be given 'directed' as a class if
            they do not already have it.
        """
        node_list = []
        for node in json_file['nodes']:
            node_instance = Node()
            _set_attributes(node_instance, node)
            node_list.append(node_instance)
        self.nodes.extend(node_list)

        edge_list = []
        if 'edges' in json_file:
            for edge in json_file['edges']:
                edge_instance = Edge()
                _set_attributes(edge_instance, edge)
                if directed and 'directed' not in edge_instance.classes:
                    edge_instance.classes += ' directed '
            self.edges.extend(edge_instance)

    def add_graph_from_df(self, df, groupby_cols, attribute_list=[], edges=tuple(), directed=False):
        """
        Converts any Pandas DataFrame in to a Cytoscape graph.
        Parameters
        ----------
        self: cytoscape graph
        df: pandas dataframe
        groupby_cols: list of strings (dataframe columns)
        attribute_list: list of strings (dataframe columns)
        edges: tuple in wich the first argument is the source edge and the
            second is the target edge
        directed: boolean
            If True all edges will be given 'directed' as a class if
            they do not already have it.
        """
        grouped = df.groupby(groupby_cols)
        group_nodes = {}
        for i, name in enumerate(grouped.groups):
            if not isinstance(name, tuple):
                name = (name,)
            group_nodes[name] = Node(data={'id': 'parent-{}'.format(i), 'name': name})

        graph_nodes = []
        graph_edges = []
        for index, row in df.iterrows():
            parent = group_nodes[tuple(row[groupby_cols])]

            # Includes content to tips
            tip_content = ''
            for attribute in attribute_list:
                tip_content += '{}: {}\n'.format(attribute, row[attribute])

            # Creates a list with all nodes adding them in the correct node parents
            graph_nodes.append(Node(data={'id': index, 'parent': parent.data['id'],
                                        'name': tip_content}))

            if not all(edges):
                # Creates a list with all nodes adding them in the correct node parents
                graph_nodes.append(Node(data={'id': index, 'parent': parent.data['id'],
                                            'name': tip_content}))

                if directed:
                    classes = 'directed '
                else:
                    classes = ''
                graph_edges.append(Edge(data={'id': index, 'source': edges[0],
                                            'target': edges[1], 'classes': classes}))

        # Adds group nodes and regular nodes to the graph object
        all_nodes = list(group_nodes.values()) + graph_nodes
        self.nodes.extend(all_nodes)

        self.edges.extend(graph_edges)


class CytoscapeWidget(DOMWidget):
    """ Implements the main Cytoscape Widget """
    _model_name = Unicode('CytoscapeModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('CytoscapeView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    # interaction options
    min_zoom = CFloat(1e-50).tag(sync=True)
    max_zoom = CFloat(1e50).tag(sync=True)
    zooming_enabled = Bool(True).tag(sync=True)
    user_zooming_enabled = Bool(True).tag(sync=True)
    panning_enabled = Bool(True).tag(sync=True)
    user_panning_enabled = Bool(True).tag(sync=True)
    box_selection_enabled = Bool(False).tag(sync=True)
    selection_type = Unicode('single').tag(sync=True)
    touch_tap_threshold = Integer(8).tag(sync=True)
    desktop_tap_threshold = Integer(4).tag(sync=True)
    autolock = Bool(False).tag(sync=True)
    auto_ungrabify = Bool(False).tag(sync=True)
    auto_unselectify = Bool(True).tag(sync=True)

    # rendering options
    headless = Bool(False).tag(sync=True)
    style_enabled = Bool(True).tag(sync=True)
    hide_edges_on_viewport = Bool(False).tag(sync=True)
    texture_on_viewport = Bool(False).tag(sync=True)
    motion_blur = Bool(False).tag(sync=True)
    motion_blur_opacity = CFloat(0.2).tag(sync=True)
    wheel_sensitivity = CFloat(1).tag(sync=True)
    cytoscape_layout = Dict({'name': 'cola'}).tag(sync=True)
    pixel_ratio = Union([Unicode(), CFloat()], default_value='auto').tag(sync=True)
    cytoscape_style = List([
                            {
                                'selector': 'node',
                                'css': {
                                    'background-color': '#11479e'
                                    }
                                },
                            {
                                'selector': 'node:parent',
                                'css': {
                                    'background-opacity': 0.333
                                    }
                                },
                            {
                                'selector': 'edge',
                                'style': {
                                    'width': 4,
                                    'line-color': '#9dbaea',
                                }
                            },
                            {
                                'selector': 'edge.directed',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle',
                                    'target-arrow-color': '#9dbaea',
                                }
                            }
                        ]).tag(sync=True)
    zoom = CFloat(2.0).tag(sync=True)
    rendered_position = Dict({'renderedPosition': { 'x': 100, 'y': 100 }}).tag(sync=True)
    tooltip_source = Unicode('tooltip').tag(sync=True)

    graph = Instance(Graph, args=tuple()).tag(sync=True, **widget_serialization)

    def __init__(self, **kwargs):
        super(CytoscapeWidget, self).__init__(**kwargs)

        self.graph = Graph()

    def set_layout(self, **kwargs):
        """
        Sets the layout of the current object. Change the parameters individually.
        For extensive documentation on the different kinds of layout please refer
        to https://js.cytoscape.org/#layouts
        Parameters
        ----------
        name: str
            name of the layout, ex.: cola, grid.
        nodeSpacing: int
            changes padding between nodes
        edgeLengthVal: int
            changes lenght of edges
        padding: int
            adds padding to the whole graph in comparison to the Jupyter's cell
        """
        dummy_dict = copy.deepcopy(self.cytoscape_layout)

        for key, value in kwargs.items():
            dummy_dict[key] = value

        self.cytoscape_layout = dummy_dict

    def get_layout(self):
        """
        Gets the layout of the current object.
        """
        return self.cytoscape_layout

    def set_style(self, style):
        """
        Sets the layout of the current object. Change the parameters
        with a dictionary.
        Parameters
        ----------
        stylesheet: dict
            See https://js.cytoscape.org for layout examples.
        """
        self.cytoscape_style = style

    def get_style(self):
        """
        Gets the style of the current object.
        """
        return self.cytoscape_style

    def set_tooltip_source(self, source):
        """
        Parameters
        ----------
        source : string
            The key in data that will be used to populate the tooltip
        """
        self.tooltip_source = source
