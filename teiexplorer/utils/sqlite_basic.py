#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
lazy_sqlite_basic is part of the project TEIExplorer
Author: Valérie Hanoka

"""

import logging
import dataset
from utils import (
    merge_two_dicts
)
from lingutils import (
    parse_year_date,
    parse_person
)
from copy import deepcopy


class CorpusSQLiteDB(object):
    """
    Class which stores in an SQLite DB the content of
    the information retrieved from the XML-TEI corpora.
    """

    logging.basicConfig(
            format='%(asctime)s : %(levelname)s : %(message)s',
            level=logging.INFO)

    db = None

    def __init__(self, db_name):
        self.db = dataset.connect(u'sqlite:///%s' % db_name)

        # Tables

        self.document_table = self.db.create_table('document',
                                                   primary_id=u'_file',
                                                   primary_type=self.db.types.string(200))

        self.idno_table = self.db.create_table('identifier')
        self.document_has_idno_table = self.db.create_table('documentHasIdentifier')

        self.date_table = self.db.create_table('date')
        self.document_has_date_table = self.db.create_table('documentHasDate')

        self.person_table = self.db.create_table('person')
        self.document_has_author_table = self.db.create_table('documentHasAuthor')

        self.title_table = self.db.create_table('title')
        self.document_has_title_table = self.db.create_table('documentHasTitle')

    def get_ordered_metadata_attributes(self, attribute_dict):
        """
        Transforms part of a TEIHeader metadata dictionary from a DocumentContent
        into a dictionnary better corresponding to our SQL schema.

        Example: The dict
        >>>{u'_#fileDesc#sourceDesc':
        >>>        {u'idno': [(6, u'-cd n348'),
        >>>                   (5, u'n348 n349 n352 n353 n354 n355 n356'),
        >>>                   (4, u'Helvi'),
        >>>                   (3, u'Helvi')],
        >>>         u'type': [(6, u'inalf2'),
        >>>                   (5, u'inalf1'),
        >>>                   (4, u'shrtcitelimit'),
        >>>                   (3, u'shrtcite')]}
        Will be transformed to:
        >>>{u'_#fileDesc#sourceDesc': {3: {u'idno': u'Helvi', u'type': u'shrtcite'},
        >>>                            4: {u'idno': u'Helvi', u'type': u'shrtcitelimit'},
        >>>                            5: {u'idno': u'n348 n349 n352 n353 n354 n355 n356',
        >>>                                u'type': u'inalf1'},
        >>>                            6: {u'idno': u'-cd n348', u'type': u'inalf2'}}}
        :param attribute_dict:
        :return:
        """
        if not attribute_dict:
            return {}
        attribute_by_source_list = []
        d = {}
        for xml_origin, attr_values_dict in attribute_dict.items():
            for (attribute, value_list) in attr_values_dict.items():
                for (counter, value) in value_list:
                    old_value = d.get(xml_origin, {})
                    new_value = {counter: {attribute: value}}
                    d[xml_origin] = merge_two_dicts(old_value, new_value)
            attribute_by_source_list.append(d)
        return d

    def _insert_document_row(self, doc):
        """Add the current document in the document_table"""
        return self.document_table.insert(doc.document_metadata)
        # TODO : Body parsing information


    def _get_or_create_row(self, row_info, table):
        """ If the information is already stored in the table table, fetch its id and returns it.
        Add it otherwise. """
        new_row = table.find_one(**row_info)
        new_row_id = new_row.get('id', None) if new_row else table.insert(row_info)
        return new_row_id

    def _insert_document_item_row(
            self,
            item=None,  # the name of the element to put in the tables
            modifier_function=None, # a function which will modify the item information
            base_table=None, # item table
            relational_table=None,  # DocumentHasItem table
            doc_info=None, # Document information
            doc_id=None # Document id in the document_table
    ):
        """Add the current document's item in the following tables:
            - item_table
            - documentHasItem_table"""

        if not (item
                and base_table is not None
                and relational_table is not None
                and doc_info
                and doc_id):
            raise ValueError("""
            Missing argument for function  _insert_document_item_row:
                item = %s,
                base_table = %s
                relational_table = %s
                doc_info = %s
                doc_id = %s """ %
                             (
                                item,
                                base_table,
                                relational_table,
                                doc_info,
                                doc_id
                             )
                             )

        item_unordered_info = doc_info.header_metadata.get(item, None)
        if not item_unordered_info:
            return
        item_info = self.get_ordered_metadata_attributes(item_unordered_info)
        for (from_xml_element, rows) in item_info.items():
            for row_number, row_info in rows.items():
                if modifier_function:
                    row_info = modifier_function(row_info)
                if not row_info:
                    continue
                new_row_id = self._get_or_create_row(row_info, base_table)

                doc_has_item_info = {
                    'document_id': doc_id,
                    '%s_id' % item: new_row_id,
                    'from_xml_element': from_xml_element
                }
                self._get_or_create_row(doc_has_item_info, relational_table)

    def add_xml_document(self, doc):
        """Saves a DocumentContent() in a SQLite database."""
        logging.info("Saving document %s in the database." % doc.document_metadata.get(u'_file'))

        # --- DOCUMENT ---- #
        document_id = self._insert_document_row(doc)

        # --- IDENTIFIER ---- #
        def add_url_type(row_info):
            idno = row_info.get(u'idno', None)
            if idno and u'http://' in idno:
                row_info[u'type'] = u'url'
            return row_info

        self._insert_document_item_row(
            item=u'idno',
            modifier_function=add_url_type,
            base_table=self.idno_table,
            relational_table=self.document_has_idno_table,
            doc_info=doc,
            doc_id=document_id
        )

        # --- DOCUMENT DATE --- #
        def normalise_date_information(row_info):

            edited_date = row_info.get(u'when', None)  # corresponds to the cleanest date information we could use
            date = edited_date if edited_date else row_info.get(u'date', None)

            parsed_info_dict = parse_year_date(date)
            row_info.update(parsed_info_dict)
            return row_info

        self._insert_document_item_row(
            item=u'date',
            modifier_function=normalise_date_information,
            base_table=self.date_table,
            relational_table=self.document_has_date_table,
            doc_info=doc,
            doc_id=document_id
        )

        # --- DOCUMENT AUTHORS --- #
        def normalise_author_information(row_info):
            authors = row_info.get('author', None)
            if not authors:
                return
            if isinstance(authors, unicode):
                row_info.update(parse_person(row_info['author']))
                return row_info
            elif isinstance(authors, list):
                authors_info = []
                row_info.pop('author')
                # pop author
                for author in authors:
                    author_row_info = deepcopy(row_info)
                    author_row_info.update(parse_person(author))
                    author_row_info['author'] = author
                    authors_info.append(author_row_info)
                return authors_info

        self._insert_document_item_row(
            item=u'author',
            modifier_function=normalise_author_information,
            base_table=self.person_table,
            relational_table=self.document_has_author_table,
            doc_info=doc,
            doc_id=document_id
        )

        # --- DOCUMENT TITLE --- #
        self._insert_document_item_row(
            item=u'title',
            base_table=self.title_table,
            relational_table=self.document_has_title_table,
            doc_info=doc,
            doc_id=document_id
        )
