#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import networkx as nx
# from networkx.readwrite import json_graph

# class CorpusGraph(object):
#
#     g = None
#
#     def __init__(self):
#         """TODO"""
#         self.g = nx.DiGraph()
#
#     #--------------------
#     #   Nodes creation
#     #--------------------
#     def createDocumentNodes(self, document_metadata):
#         """TODO"""
#
#         # File unique id will be its filepath
#         # A document is a node.
#         corpus_tag = document_metadata.pop(u'corpus_tag', 'UNK') # TODO Change the pop and labels
#         file_path = document_metadata.pop(u'filePath', 'UNK')# TODO Change
#         idno = document_metadata.pop(u'idno', 'UNK') # TODO Change
#
#         document = self.g.add_node(file_path, origin=corpus_tag, idno=idno)
#
#         # Each document attribute will be another typed node, linked to the Document Node
#         # Nodes must be unique in the graph.
#         for attribute_type in document_metadata:
#             attribute_content = document_metadata[attribute_type]
#             # TODO Make it unique
#             if not (attribute_content in self.g.nodes() and self.g.node[attribute_content] is attribute_type):
#                 attribute = self.g.add_node(attribute_content, vtype=attribute_type)
#
#             self.g.add_edge(file_path, attribute_content, etype=attribute_type)
#
#
#
#     def saveToPng(self, output_file):
#         """TODO"""
#         #import ipdb; ipdb.set_trace()
#         import matplotlib
#         matplotlib.use("Agg")
#         import matplotlib.pyplot as plt
#         fig = plt.figure()
#         nx.draw(self.g, ax=fig.add_subplot(111))
#         fig.savefig(output_file)
#         print u"Dumped in %s" % output_file
#
#     def saveToGraphml(self, output_file):
#         """TODO"""
#         nx.write_graphml(self.g, output_file, encoding='utf-8')
#         print u"Dumped in %s" % output_file
#
#     def loadGraphml(self, input_file):
#         """TODO"""
#         import pdb;
#         pdb.set_trace()
#         #self. g = nx.read_graphml(input_file, unicode)

