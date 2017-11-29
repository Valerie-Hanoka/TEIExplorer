#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sql_basic is part of the project obvil
Author: Valérie Hanoka

"""
from functools import wraps
import sqlalchemy
from sqlalchemy import (
    Column,
    Integer,
    String,
    VARCHAR,
    DATE,
    ForeignKey,
    Boolean,
    MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def fixed_batch_commit(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._COUNTER += 1
        func(self, *args, **kwargs)
        if self._COUNTER % self.batch_size == 0:
            self.session.commit()

    return wrapper


class CorpusSQLiteDB(object):
    """
    Class which stores in an SQLite DB the content of
    the information retrieved from the XML-TEI corpora.
    """

    Base = declarative_base()
    db = None
    metadata = None
    connexion = None
    session = None

    batch_size = 1
    _COUNTER = 0


    class Document(Base):
        __tablename__ = "document"

        id = Column(VARCHAR(200), primary_key=True)
        tag = Column(VARCHAR(100), nullable=False)
        is_body_parsed = Column(Boolean)
        publisher = Column(VARCHAR(100))
        publication_place = Column(VARCHAR(50))
        editor = Column(VARCHAR(100))
        url = Column(VARCHAR(100))
        doc_idno = Column(VARCHAR(200))

        def __init__(self, kwargs):
            for k, v in kwargs.items():
                if type(v) is list:
                    v = None if len(v) == 0 else v.pop()
                self.__setattr__(k, v)

    class Person(Base):
        """"""
        __tablename__ = "person"

        id = Column(Integer, primary_key=True)
        raw_name = Column(String, nullable=False)
        first_name = Column(VARCHAR(200))
        last_name = Column(VARCHAR(200))
        title = Column(VARCHAR(100))  # E.g. Mister, Doctor, ...
        birth_year = Column(DATE)
        death_year = Column(DATE)

    class DocumentHasAuthor(Base):
        __tablename__ = 'documentHasAuthor'

        id = Column(Integer, primary_key=True)
        document_id = Column(VARCHAR(200), ForeignKey('document.id'))
        person_id = Column(Integer, ForeignKey('person.id'))

    class DocumentHasTitle(Base):
        __tablename__ = 'documentHasTitle'

        id = Column(Integer, primary_key=True)
        document_id = Column(VARCHAR(200), ForeignKey('document.id'))
        title = Column(String)
        title_type = Column(VARCHAR(100))

    class DocumentHasDate(Base):
        __tablename__ = 'documentHasDate'

        id = Column(Integer, primary_key=True)
        document_id = Column(VARCHAR(200), ForeignKey('document.id'))
        date = Column(DATE)
        date_part_millennium = Column(Integer)
        date_part_decade = Column(Integer)
        date_part_year = Column(Integer)
        date_type = Column(VARCHAR(100))

    def __init__(self, db_name):

        self.connexion = sqlalchemy.create_engine(u'sqlite:///%s' % db_name)
        self.metadata = MetaData(bind=self.connexion, reflect=True)
        self.Base.metadata.create_all(self.connexion)
        DBsession = sessionmaker(bind=self.connexion)
        self.session = DBsession()

    def finalise(self):

        # Commit the last things
        self.session.commit()

        # Close communication with the database
        self.session.close()



    @fixed_batch_commit
    def add_xml_document(self, doc):


        # # Adding information to the document Table
        # document_info = {
        #     'id': doc.document_metadata[u'_file'],
        #     'tag': doc.document_metadata[u'_tag'],
        #     'is_body_parsed': doc.document_metadata[u'_body_parsed'],
        #     'publisher': doc.header_metadata.get(u'publisher', None),
        #     'publication_place': doc.header_metadata.get(u'pubPlace', None),
        #     'editor': doc.header_metadata.get(u'editor', None),
        #     'url': doc.header_metadata.get(u'url', None),
        #     'doc_idno': doc.header_metadata.get(u'idno', None)
        # }
        # new_document = self.Document(document_info)
        # self.session.add(new_document)

        # Title information



        # filedesc_title_info = {
        #     'xml_parent': u'fileDesc',
        #     'title': doc.document_metadata.get(u'fileDesc:title'),
        #     'type': doc.document_metadata.get(u'title:type'),
        #     'level': doc.document_metadata.get(u'fileDesc:title:level')
        # }
        #
        # sourcedesc_title_info = {
        #     'xml_parent': u'sourceDesc',
        #     'title': doc.document_metadata.get(u'sourceDesc:title'),
        #     'type': doc.document_metadata.get(u'sourceDesc:title:type'),
        #     'level': doc.document_metadata.get(u'sourceDesc:title:level')
        # }
        #
        # # Adding authors
        # filedesc_author_info = {
        #     'xml_parent': u'fileDesc',
        #     'author': doc.document_metadata.get(u'fileDesc:author'),
        #     'key': doc.document_metadata.get(u'fileDesc:author:key'),
        #     'role': doc.document_metadata.get(u'fileDesc:author:role'),
        #     'type': doc.document_metadata.get(u'fileDesc:author:type'),
        # }
        #
        # sourcedesc_author_info = {
        #     'xml_parent': u'fileDesc',
        #     'author': doc.document_metadata.get(u'sourceDesc:author'),
        #     'key': doc.document_metadata.get(u'sourceDesc:author:key'),
        #     'role': doc.document_metadata.get(u'sourceDesc:author:role'),
        #     'type': doc.document_metadata.get(u'sourceDesc:author:type'),
        # }


        #doc_authors = doc.header_metadata[u'author']  # [u'Diderot, Denis, 1713-1784.'],
        #new_author = self.Person(name='new person')

        # Adding Titles
        #doc_title = doc.header_metadata[u'title']  # [u'titre recueuil', u'Les Amours', u'[Les] Amours']


        # Adding dates
        #doc_date = doc.header_metadata[u'date'] #: [u'20#06', u'15#52', u'19#98', u'15#52'],



        print self._COUNTER




    def _add_document(self, metadata, body_metrics):

        line = {}
        for k, v in metadata.iteritems():
            if k == '_file':
                line['location'] = v
            elif k == 'title' or k == 'editor':
                line[k] = v
            else:
                print "WARNING (ignored): %s:%s " % (k,v)
            i = self.document.insert()

            # Column('book', Integer, ForeignKey('book.id')),
            # Column('datePublished', Integer, ForeignKey('date.id'))


    # def _add_authors(self, author_info):
    #     return authors_keys
    #
    # def _add_book(self, document):
    #     return book_key


    # def _create_tables(self):
    #
    #     self.document = Table(
    #         'document', self.metadata,
    #         Column('location', String, primary_key=True),
    #         Column('title', String),
    #         Column('editor', VARCHAR(100)),
    #         Column('book', Integer, ForeignKey('book.id')),
    #         Column('datePublished', DATE)  # TODO , ForeignKey('date.id')
    #     )
    #
    #     self.book = Table(
    #         'book', self.metadata,
    #         Column('book_id', Integer, primary_key=True),
    #         Column('title', String, nullable=False),
    #         Column('url', VARCHAR(100))
    #     )
    #
    #     self.person = Table(
    #         'person', self.metadata,
    #         Column('person_id', Integer, primary_key=True),
    #         Column('raw_name', String, nullable=False),
    #         Column('first_name',  VARCHAR(100)),
    #         Column('last_name',  VARCHAR(100)),
    #         Column('title',  VARCHAR(100)),  # E.g. Mister, Doctor, Father...
    #         Column('birth_year', DATE),
    #         Column('death_year', DATE),
    #     )
    #
    #     self.book_has_author = Table(
    #         'book_has_author', self.metadata,
    #         Column('id', Integer, primary_key=True),
    #         Column('book_id', Integer, ForeignKey("book.book_id"), nullable=False),
    #         Column('person_id', Integer, ForeignKey("person.person_id"), nullable=False)
    #     )
    #
    #     self.document_is_book = Table(
    #         'book_has_author', self.metadata,
    #         Column('id', Integer, primary_key=True),
    #         Column('document_id', Integer, ForeignKey("person.person_id"), nullable=False),
    #         Column('book_id', Integer, ForeignKey("book.book_id"), nullable=False),
    #         Column('type_of_subsumption', Enum('whole', 'part', 'unkwn'))
    #     )
    #
    #     self.metadata.create_all(self.connexion)



