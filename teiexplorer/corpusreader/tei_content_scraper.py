#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from collections import Counter
from lxml import etree
from nltk.stem.snowball import SnowballStemmer
from textblob import TextBlob

from teiexplorer.utils.utils import merge_two_dicts
from teiexplorer.utils.lingutils import (
    normalise_date,
    is_content_word
)


class DocumentContent(object):

    logging.basicConfig(
            format='%(asctime)s : %(levelname)s : %(message)s',
            level=logging.INFO)

    filePath = None

    document_metadata = {}
    header_metadata = {}
    body_metadata = {}

    blob = None
    content_words = []
    
    def __init__(self, document_filepath, corpus_tag, stemming=True, *args, **kwargs):
        """ A generic Document representation which keeps track of
        metadata for header and textual content of a file.
        This object describes the content of a document.
        This document object stores its information in 3 main places:
            - document_metadata, which describe the type and location of the document
            - header_metadata, which describes the header content of the document
            - body_metadata, which stores some computed information about the body of the document
        It also contains "blobby" information on the content of the document (list of content words,...).
        :param document_filepath: :String: The document file path to parse
        :param corpus_tag: The tag of the corpus from which the document comes
        :param stemming: :Boolean: Enable stemming
        :param args:
        :param kwargs:
        """
        self.filePath = document_filepath
        self.stemming = stemming

        # Additional metadata
        self.document_metadata[u'_file'] = unicode(document_filepath)
        self.document_metadata[u'_tag'] = unicode(corpus_tag)


class TeiContent(DocumentContent):

    namespace = ''
    etree_xml = None
    etree_root = None

    def __init__(self, document_filepath, corpus_tag, stemming=True, *args, **kwargs):
        """
        A generic TEI Parser which collects the header metadata of a file,
        and a representation of its body.
        :param document_filepath: The TEI document file path to parse
        :param corpus_tag: The tag of the corpus from which the document comes
        :param stemming: :Boolean: Enable stemming
        :param args:
        :param kwargs:
        """

        super(TeiContent, self).__init__(document_filepath, corpus_tag, stemming,  *args, **kwargs)

        self.__initialise_parser()

        if self.etree_xml:
            self.__parse_header()
            self.__get_body_metrics()

    def __initialise_parser(self):
        """Initialization of the XML/TEI parser for current document
        """
        # cf. http://lxml.de/3.7/parsing.html
        utf8_parser = etree.XMLParser(
            remove_blank_text=True,
            encoding='utf-8',
            # load_dtd=True,
            recover=True)

        try:
            self.etree_xml = etree.parse(self.filePath, parser=utf8_parser)
            self.namespace = '{' + self.etree_xml.xpath('namespace-uri(.)') + '}'
        except etree.XMLSyntaxError:
            logging.warning("Ignoring file %s" % self.filePath)

    ######################
    #      HEADERS
    ######################

    def __parse_header(self):
        """Parses the header of an xml (or tei) document.
        It keeps all the attributes-values pairs encoded in the header,
        except for those explicitly excluded by the self.__clean_metadata()
        method.
        the result for the current document is stored in self.metadata."""

        # Parsing the document header
        self.etree_root = self.etree_xml.getroot()
        metadata_root = self.etree_root.find(self.namespace + "teiHeader")
        self.header_metadata = merge_two_dicts(
            self.header_metadata,
            self.__recursive_tag_info_retriever(metadata_root)
        )

        # Cleaning useless or empty entries
        self.__clean_metadata()

    def __recursive_tag_info_retriever(self, element):
        """
        Dive into a xml element to retrieve all the information from
        it and its children.
        :param element: :String: An xml element of the TEI document to parse
        :return: The textual information contained in the element
        """

        element_information = {}
        elements_iterator = element.getchildren()

        for child in elements_iterator:
            if child.getchildren():
                element_information = merge_two_dicts(
                    self.__recursive_tag_info_retriever(child),
                    element_information
                )
            else:
                if child.text:
                    (normalized_text, normalized_tag) = self.__normalize_metadata(child.text, child.tag)
                    element_information[normalized_tag] = normalized_text
                    for attribute_key, attribute_value in child.attrib.items():
                        (normalized_attribute_value, normalized_attribute_key) =\
                            self.__normalize_metadata(attribute_value, normalized_tag + ":" + attribute_key)
                        element_information[normalized_attribute_key] = normalized_attribute_value

        return element_information

    def __normalize_metadata(self, value, key):
        """When parsing key - values pairs from the XML metadata,
        we want to ensure that:
            - the encoding is consistent (use of unicode everywhere)
            - we use the compact key (without the namespace)
        :param value: unicode, cleaned value
        :param key: clean key version"""
        # Using unicode
        value = unicode(value)
        key = unicode(key)

        if key.startswith(self.namespace):
            key = key[len(self.namespace):]

        # Removing multiple spaces, newlines, carriage returns, tabs...
            value = ' '.join(value.split())

        # Dates
        if u'date' in key:
            value = normalise_date(value)

        return value, key

    def __clean_metadata(self):
        """Once the metadata dictionary is completed, we want to be sure that
         it only contain relevant information. This part is very heuristic,
         and should be redefined in later versions"""

        # TODO
        # accepted_keys = [
        #     "_file",
        #     "_tag",
        #     "author",
        #     "title",
        #     "date",
        #     "_words",
        #     "_sentences",
        #     "_chars",
        #     "_tokens",
        #     "_sent:polarity",
        #     "_sent:subjectivity"
        # ]

        unwanted_keys = ['^note$', '^..?$', '^.*at 0x.*$', '^projectDesc.*$']
        unwanted_values = ['^$', '^CONVERT-TARGET:.*$']

        unwanted_keys_re = re.compile('|'.join('(?:%s)' % p for p in unwanted_keys))
        unwanted_values_re = re.compile('|'.join('(?:%s)' % p for p in unwanted_values))

        matched_unwanted_keys = [
            k for k, v in self.header_metadata.items()
            if unwanted_keys_re.match(k) or unwanted_values_re.match(v)]

        for k in matched_unwanted_keys:
            del self.header_metadata[k]

    ######################
    #   CONTENT METRICS
    ######################
    def __get_body_metrics(self):
        """Computes various metrics on the text body of the XML/TEI document:
            • Number of characters
            • Number of tokens
            • Number of words
            • Number of sentences
            • A (not reliable) polarity score
            • A (not reliable) subjectivity score
        """

        tag = ".//%sbody" % self.namespace
        bodies = self.etree_xml.find(tag)
        if bodies is None:
            logging.warning("File %s body is ill-formed. Not Parsing it." % self.filePath)
            self.document_metadata[u'_body_parsed'] = False
            return
        for body in bodies:
            text_pieces = [t for t in body.itertext()]
            self.blob = TextBlob(' '.join(text_pieces))
            self.__initialise_content_words()
            self.body_metadata[u"_chars"] = len(self.blob)
            self.body_metadata[u"_words"] = len(self.blob.words)
            self.body_metadata[u"_sentences"] = len(self.blob.sentences)
            self.body_metadata[u"_sent:polarity"] = \
                round(self.blob.sentiment.polarity, 3)  # within [-1, 1]
            self.body_metadata[u"_sent:subjectivity"] = \
                round(self.blob.sentiment.subjectivity, 3)  # [0=很objective, 1=很subjective]
            self.document_metadata[u'_body_parsed'] = True
            try:
                self.body_metadata[u"_tokens"] = len(self.blob.tokens)
            except LookupError:
                import nltk
                nltk.download('punkt')
                self.body_metadata[u"_tokens"] = len(self.blob.tokens)

    def get_text_content_word_count(self):
        """Gets the word counts of words in the text that are not in the stopword list
        :return: """
        if self.blob:
            return Counter(self.content_words)
        else:
            logging.debug(u"%s won't be taken into account " % self.filePath)
            return {}

    def __initialise_content_words(self):
        """
        TODO - proper normalisation
        Returns a list of normalized content words (no punctuation)
        normalized here means just lower case + stemmed if the option
        is enabled.
        :return: A list of normalized content words."""
        if self.blob:

            if self.stemming:
                stemmer = SnowballStemmer("french")
                self.content_words = [
                    unicode(stemmer.stem(w.lower()))
                    for w in self.blob.tokens
                    if is_content_word(w)
                ]
            else:
                self.content_words = [
                    unicode(w.lower())
                    for w in self.blob.tokens
                    if is_content_word(w)
                ]



