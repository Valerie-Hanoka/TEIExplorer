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
from pylru import lrudecorator

class CorpusSQLiteDBWriter(object):
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

        if not self.db.tables:
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

        else:
            self.document_table = self.db['document']
            self.idno_table = self.db['identifier']
            self.document_has_idno_table = self.db['documentHasIdentifier']

            self.date_table = self.db['date']
            self.document_has_date_table = self.db['documentHasDate']

            self.person_table = self.db['person']
            self.document_has_author_table = self.db['documentHasAuthor']

            self.title_table = self.db['title']
            self.document_has_title_table = self.db['documentHasTitle']



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



        ark_id_dict = doc.header_metadata.get('ark')
        if ark_id_dict:
            _, ark_id = ark_id_dict.values().pop().get('ark')[0]
            doc.document_metadata['ark'] = ark_id
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


    # ----  Transforming Information for table modification  ----#

    def modify_url_type(self, row_info):
        idno = row_info.get(u'idno', None)
        if idno and u'http://' in idno:
            row_info[u'type'] = u'url'
        return row_info

    def normalise_date_information(self, row_info):
        edited_date = row_info.get(u'when', None)  # corresponds to the cleanest date information we could use
        date = edited_date if edited_date else row_info.get(u'date', None)

        parsed_info_dict = parse_year_date(date)
        row_info.update(parsed_info_dict)
        return row_info

    def normalise_author_information(self, row_info):
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

    def add_xml_document(self, doc):
        """Saves a DocumentContent() in a SQLite database."""
        logging.info("Saving document %s in the database." % doc.document_metadata.get(u'_file'))

        # --- DOCUMENT ---- #
        document_id = self._insert_document_row(doc)

        # --- IDENTIFIER ---- #
        self._insert_document_item_row(
            item=u'idno',
            modifier_function=self.modify_url_type,
            base_table=self.idno_table,
            relational_table=self.document_has_idno_table,
            doc_info=doc,
            doc_id=document_id
        )

        # --- DOCUMENT DATE --- #
        self._insert_document_item_row(
            item=u'date',
            modifier_function=self.normalise_date_information,
            base_table=self.date_table,
            relational_table=self.document_has_date_table,
            doc_info=doc,
            doc_id=document_id
        )

        # --- DOCUMENT AUTHORS --- #
        self._insert_document_item_row(
            item=u'author',
            modifier_function=self.normalise_author_information,
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


class CorpusSQLiteDBReader(object):


    logging.basicConfig(
            format='%(asctime)s : %(levelname)s : %(message)s',
            level=logging.INFO)

    db = None

    def __init__(self, db_name):
        self.db = dataset.connect(u'sqlite:///%s' % db_name)

        # Checking that we have every necessary column in the DB
        try:

            expected_tables = {u'date',
                               u'document',
                               u'documentHasAuthor',
                               u'documentHasDate',
                               u'documentHasIdentifier',
                               u'documentHasTitle',
                               u'identifier',
                               u'person',
                               u'title'}
            assert len(expected_tables-set(self.db.tables)) == 0
        except AssertionError:
            raise IOError("Database does not correspond to what is expected.")

        self.document_table = self.db['document']
        self.idno_table = self.db['identifier']
        self.document_has_idno_table = self.db['documentHasIdentifier']
        self.date_table = self.db['date']
        self.document_has_date_table = self.db['documentHasDate']
        self.person_table = self.db['person']
        self.document_has_author_table = self.db['documentHasAuthor']
        self.title_table = self.db['title']
        self.document_has_title_table = self.db['documentHasTitle']

    def treat_document(self):

        for document in self.document_table:
            doc_id = document['_file']
            doc_info = self.get_document_information_in_db(doc_id)

            import pprint
            pprint.pprint(doc_info)


    def get_document_information_in_db(self, doc_id):
        """Iterates over all the documents SQLite database."""

        info = dict()
        info['authors'] = self._get_normalised_authors(doc_id)
        info['date'] = self._get_earliest_dates(doc_id)
        info['title'] = self._get_full_title(doc_id)

        # Computing age of the eldest author at the first publication date
        if info.get('authors') and info.get('date'):
            try:
                eldest_author_birth_year = \
                    int(
                        sorted([y.get('birth', '99999')
                                for y in info.get('authors').values()])[0])
                pub_date = int(info.get('date'))
                if 1 < eldest_author_birth_year < 2000 and pub_date:
                    info['age_at_publication'] = pub_date - eldest_author_birth_year
            except ValueError:
                pass

        return info



    def _get_full_title(self, doc_id):

        raw_titles = [
            self.title_table.find_one(id=doc_has_title['title_id'])
            for doc_has_title
            in self.document_has_title_table.find(document_id=doc_id)
        ]

        seen_titles = {}
        titles = []
        for raw_title in raw_titles:
            t = raw_title.get('title', None)
            if t:
                is_present = seen_titles.get(t.lower(), None)
                if not is_present:
                    titles.append((raw_title.get('level', u'ȥ') or u'ȥ', t))
                    seen_titles[t.lower()] = 1
            else:
                print("%s is present already" %t)
        
        concatenated_title = u' — '.join([ title for (_, title) in sorted(titles, reverse=True)])
        return concatenated_title

    def _get_earliest_dates(self, doc_id):

        db_dates = [
            self.date_table.find_one(id=doc_has_date['date_id'])
            for doc_has_date
            in self.document_has_date_table.find(document_id=doc_id)
        ]

        if not db_dates:
            return

        dates = set([])
        for date in db_dates:
            try:
                int(date.get('deduced_date'))
                dates.add(date.get('deduced_date'))
            except TypeError:
                # Partial dates
                m = int(date.get('millennium', '-1'))
                c = int(date.get('century', '-1'))
                d = int(date.get('decade', '-1'))
                y = int(date.get('year', '-1'))

                m = str(m) if m > -1 else ' '
                c = str(c) if c > -1 else ' '
                d = str(d) if d > -1 else ' '
                y = str(y) if y > -1 else ' '
                deduced_date = "%s%s%s%s" % (m, c, d, y)
                dates.add(int(deduced_date.strip()))

        earliest = str(sorted(dates)[0])
        while len(earliest) < 4:
            earliest = "%s." % earliest

        return earliest

    def _get_normalised_authors(self, doc_id):
        doc_authors = [
            self.person_table.find_one(id=doc_has_author['author_id'])
            for doc_has_author
            in self.document_has_author_table.find(document_id=doc_id)
        ]

        if not doc_authors:
            return

        fingerprint_info = {
            author.get('fingerprint'): {'role':  author.get('role')}
            for author in doc_authors
        }


        for fingerprint in fingerprint_info:
            fingerprint_info[fingerprint] = self._reconcile_fingerprints(fingerprint)
        return fingerprint_info


    @lrudecorator(300)
    def _reconcile_fingerprints(self, fingerprint):

        similar_authors = [p for p in self.person_table.find(fingerprint=fingerprint)]

        ignore_info = ['id', 'role', 'fingerprint']
        # For all the similar authors (i.e: same fingerprints),
        # we chose to keep the one displaying the most information
        reconciled = sorted(similar_authors, key=lambda x: len(x['author']))[-1]
        info = dict()
        for (k, v) in reconciled.items():
            if k in ignore_info or not v:
                continue
            info[k] = v
        return info

