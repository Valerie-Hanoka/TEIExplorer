#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sql_basic is part of the project obvil
Author: Valérie Hanoka

"""

import dataset

class CorpusSQLDB(object):
    """
    A quick and dirty class which stores in an SQLite DB the content of
    the information retrieved from the XML-TEI corpora.
    """
    # TODO: Batch commit + Space optimization (sql types)

    db = None

    def __init__(self, db_name):
        self.db = dataset.connect('sqlite:///%s' % db_name)

        # Tables
        self.documents_table = self.db.create_table(
            'Documents',
            primary_id='_file',
            primary_type=self.db.types.string(125))
        self.body_metadata_table = self.db.create_table(
            'BodyMetadata',
            primary_id='_file',
            primary_type=self.db.types.string(125))
        self.authors_table = self.db.create_table(
            'Authors',
            primary_id='_file',
            primary_type=self.db.types.string(125))
        self.titles_table = self.db.create_table(
            'Titles',
            primary_id='_file',
            primary_type=self.db.types.string(125))

    def add_document(self, document):
        """
        The information about a document (represented by a DocumentContent object)
        is stored in 3 main places:
            - document_metadata, which describe the type and location of the document
            - header_metadata, which describes the header content of the document
            - body_metadata, which stores some computed information about the body of the document
        In order to persist this information in a usable way for the corpus exploration,
        we would rather organise the information semantically (by types):
            • Generic metadata (in the Documents table)
            • Author(s) information
            • Title(s) information
            • Content (body) metrics
        :param document: The document information to persist in the DB
        :return:
        """

        # Key for all tables
        document_file = document.document_metadata[u'_file']

        # -- Authors --
        authors_info = {
            k: v
            for k, v in document.header_metadata.iteritems()
            if 'author' in k}
        authors_info[u'_file'] = document_file
        self.authors_table.insert(authors_info)

        # -- Titles --
        title_info = {
            k: v
            for k, v in document.header_metadata.iteritems()
            if 'title' in k}
        title_info[u'_file'] = document_file
        self.titles_table.insert(title_info)

        # -- Documents --
        # Everything except the author and title information
        author_and_title = authors_info.keys() + title_info.keys()
        doc_metadata = {
            k: v
            for k, v in document.header_metadata.iteritems()
            if k not in author_and_title}
        doc_metadata.update(document.document_metadata)
        self.documents_table.insert(doc_metadata)

        # -- BodyMetadata --
        document.body_metadata[u'_file'] = document_file
        self.body_metadata_table.insert(document.body_metadata)




