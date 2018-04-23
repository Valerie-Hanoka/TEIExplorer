#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from collections import Counter
from lxml import etree
from nltk.stem.snowball import SnowballStemmer
from textblob import TextBlob

from teiexplorer.utils.utils import (
    merge_two_dicts,
    flatten_nested_dict_to_pairs
)
from teiexplorer.utils.lingutils import is_content_word


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

    logging.basicConfig(
            format='%(asctime)s : %(levelname)s : %(message)s',
            level=logging.INFO)

    namespace = ''
    etree_xml = None
    etree_root = None

    _ATTR_CMPT = 0

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
            #self.__get_body_metrics()



    def __initialise_parser(self):
        """Initialization of the XML/TEI parser for current document
        """
        # cf. http://lxml.de/3.7/parsing.html
        utf8_parser = etree.XMLParser(
            remove_blank_text=True,
            encoding='utf-8',
            # load_dtd=True,
            recover=True)
        self._ATTR_CMPT = 0

        try:
            self.etree_xml = etree.parse(self.filePath, parser=utf8_parser)
            self.namespace = '{' + self.etree_xml.xpath('namespace-uri(.)') + '}'
        except etree.XMLSyntaxError:
            logging.error(u"Ignoring file %s - XMLSyntaxError" % self.filePath)

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
        metadata_root = self.etree_root.find(self.namespace + u'teiHeader')
        self.header_metadata = merge_two_dicts(
            self.header_metadata,
            self.__recursive_tag_info_retriever(u'', metadata_root)
        )

        # Adding Ark identifier if it exists
        ark_id = self.etree_root.attrib.get('{http://www.w3.org/XML/1998/namespace}id', None)
        if ark_id:
            self.header_metadata[u'ark'] = (0, ark_id)

        # Cleaning useless or empty entries
        self.__clean_metadata()

    def __recursive_tag_info_retriever(self, parent_tag, element):
        """
        Dive into a xml element to retrieve all the information from
        it and its children.
        :param element: :String: An xml element of the TEI document to parse
        :return: The textual information contained in the element
        """
        element_information = {}
        elements_iterator = element.getchildren()
        element_tag = element.tag.rsplit('}', 1)[-1]
        element_tag = u'_' \
            if element_tag == u'teiHeader'\
            else u'%s#%s' % (parent_tag, element_tag)

        for child in elements_iterator:
            has_child = child.getchildren()
            # The node is not a leaf
            if has_child:
                if 'rend=' not in child.attrib: # If the child element is only there for rendering
                    has_child = False
                    element_information = merge_two_dicts(
                        self.__recursive_tag_info_retriever(element_tag, child),
                        element_information
                    )
            # The node is a leaf
            if not has_child:
                if child.text:
                    try:
                        text = u''.join(child.itertext())
                    except ValueError:
                        text = child.text
                    (normalized_text, normalized_tag) = self.__normalize_metadata(text, child.tag)

                    element_information = merge_two_dicts(
                        {u'%s#%s' % (element_tag, normalized_tag): (self._ATTR_CMPT, normalized_text)},
                        element_information
                    )
                    for attribute_key, attribute_value in child.attrib.items():
                        (normalized_attribute_value, normalized_attribute_key) =\
                            self.__normalize_metadata(attribute_value, normalized_tag + ':' + attribute_key)
                        element_information = merge_two_dicts(
                            {u'%s#%s' % (element_tag, normalized_attribute_key):
                                 (self._ATTR_CMPT, normalized_attribute_value)},
                            element_information
                        )
                    self._ATTR_CMPT += 1
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
            value = u' '.join(value.split())

        return value, key

    def __clean_metadata(self):
        """Once the metadata dictionary is completed, we want to be sure that
         it only contain relevant information. This part is very heuristic, quite dirty
         and should be redefined in later versions"""

        # TODO
        # accepted_keys = [ "_file", "_tag", "author", "title", "date", "_words",
        # "_sentences", "_chars", "_tokens", "_sent:polarity", "_sent:subjectivity"
        # ]

        unwanted_keys = ['^note$', '^..?$', '^.*at 0x.*$', '^hi$', '^rend$']  # , '^projectDesc.*$']
        unwanted_values = ['^$', '^CONVERT-TARGET:.*$', 'ARTFL Frantext']

        unwanted_keys_re = re.compile(u'|'.join('(?:%s)' % p for p in unwanted_keys))
        unwanted_values_re = re.compile(u'|'.join('(?:%s)' % p for p in unwanted_values))

        # Removing unwanted_values
        for k, values in self.header_metadata.items():
            if not isinstance(values, list):
                values = [values]
            kept_values = [(c, v) for (c, v) in values if v and not unwanted_values_re.match(v)]
            self.header_metadata[k] = kept_values

        # Removing unwanted keys
        matched_unwanted_keys = [
            k for k, v in self.header_metadata.items()
            if unwanted_keys_re.match(k) or len(v) == 0]

        for k in matched_unwanted_keys:
            del self.header_metadata[k]

        self._transform_header_metadata_with_keyword()

    def _transform_header_metadata_with_keyword(self):
        """ In order to be able to access easily each type of information,
         this function ensures that the key of the metadata dict is a simple entrypoint
         (eg. author, title, date...), and the values are detailed by types
         (parents in the xml as well as the attributes). For instance, the xml:

         <teiHeader>
            <fileDesc>
               <titleStmt>
                  <title>Histoire de l'Academie françoise ...</title>
                  <author role="Auteur du texte" key="11918095">Olivet, Pierre-Joseph d' (1682-1768)</author>
                  <author role="Auteur du texte" key="12180933">Pellisson-Fontanier, Paul (1624-1693)</author>
               </titleStmt>
               <publicationStmt>
                  <publisher>TGB (BnF – OBVIL)</publisher>
               </publicationStmt>
               <seriesStmt>
                  <title level="s">Histoire de l'Academie françoise ...</title>
                  <title level="a">Tome 1</title>
                  <biblScope unit="volumes" n="2" />
                  <idno>cb32496228k</idno>
               </seriesStmt>
               <sourceDesc>
                  <bibl>
                     <idno>http://gallica.bnf.fr/ark:/12148/bpt6k96039981</idno>
                     <publisher>Jean-Baptiste Coignard fils</publisher>
                     <date when="1729">1729</date>
                  </bibl>
               </sourceDesc>
            </fileDesc>
         </teiHeader>

        should have the following self.header_metadata representation:
        {
            u'author': {u'#fileDesc': {u'author': [u'Pellisson-Fontanier, Paul (1624-1693)',
                                                   u"Olivet, Pierre-Joseph d' (1682-1768)"]},
            u'key': [u'12180933', u'11918095'],
            u'role': [u'Auteur du texte', u'Auteur du texte']},
            u'date': {u'#fileDesc#sourceDesc': {u'date': [u'17#29']},
                                                u'when': [u'17#29']},
            u'idno': {u'#fileDesc':
                            {u'idno': [u'cb32496228k']},
                      u'#fileDesc#sourceDesc':
                            {u'idno': [u'http://gallica.bnf.fr/ark:/12148/bpt6k96039981']}},
            u'publisher': {u'#fileDesc': {u'publisher': [u'TGB (BnF \u2013 OBVIL)']},
            u'#fileDesc#sourceDesc': {u'publisher': [u'Jean-Baptiste Coignard fils']}},
            u'title': {u'#fileDesc': {u'title': [u'Tome 1',
                                                 u"Histoire de l'Academie fran\xe7oise ...",
                                                 u"Histoire de l'Academie fran\xe7oise ..."]},
            u'level': [u'a', u's']}
        }

        """

        new_dic = {}
        for (k, v) in self.header_metadata.items():
            if v:
                (xml_parent, _, xml_key_with_optional_attribute) = k.rpartition('#')
                if ':' in xml_key_with_optional_attribute:
                    xml_key, _, xml_attribute = xml_key_with_optional_attribute.rpartition(':')
                else:
                    (xml_key, xml_attribute) = (xml_key_with_optional_attribute, xml_key_with_optional_attribute)

                current_attribute_dict = {xml_key: {xml_parent: {xml_attribute: v}}}
                new_dic = merge_two_dicts(new_dic, current_attribute_dict)

        self.header_metadata = new_dic


    #########################
    #  ADDING CONTENT TO TEI
    #########################

    def add_to_header(self, info_dict, file_suffix='_r'):
        """Add the XML representation of info_dict in the header of the current
         TEI Document"""

        metadata_root = self.etree_root.find(self.namespace + u'teiHeader')
        additional_info_tag = etree.Element("xenoData")
        metadata_root.append(additional_info_tag)
        self.add_to_xml(info_dict, parent=additional_info_tag)
        (name, sep, ext) = self.filePath.rpartition('.')
        new_filepath = "%s%s.%s" % (name, file_suffix, ext)
        self.etree_xml.write(
            new_filepath,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=False)


    def add_to_xml(self, info_dict, parent):
        """Add the XML representation of info_dict under the
         parent in  the current TEI Document"""

        for info_key, info_value in info_dict.iteritems():
            new_sub_element = etree.Element(info_key)
            if isinstance(info_value, dict):
                self.add_to_xml(info_value, new_sub_element)

            else:
                if isinstance(info_value, int) or isinstance(info_value, float):
                    new_sub_element.text = str(info_value)
                else:
                    new_sub_element.text = info_value
            parent.append(new_sub_element)
        return parent



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
        if bodies is None or not bodies.keys(): # TODO not parsed at all
            self.document_metadata[u'_body_parsed'] = False
            logging.debug("File %s body is ill-formed. Not Parsing it." % self.filePath)
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


    ######################################################
    #                  EXPORTING DATA
    ######################################################
    def __header_to_omeka_dict(self):
        """
        Reformats (flattens+clean+regroup some elements) the header meta-data dict
        and returns a dict that will be easy to transform into a csv line.
        :return: A dict
        """

        flattened_header_metadata = [
            (k, sorted(v))
            for (k, v) in flatten_nested_dict_to_pairs(self.header_metadata)
            if 'hi__#' not in k
        ]

        flattened_header_metadata = sorted(
            flattened_header_metadata,
            key=lambda x: x[1]
        )

        by_xpath = {}
        for (key, value) in flattened_header_metadata:

            match = re.match(r'^(?P<chunkA>[^_]*)__(?P<path>[^_]*)_(?P<chunkB>[^_]*)$', key)
            if match:
                path = match.groupdict().get("path")
                chunkb = match.groupdict().get("chunkB")
                elem = by_xpath.get(path, {})
                if elem:
                    elem.update({chunkb: value})
                else:
                    elem = {chunkb: value}
                by_xpath[path] = elem

        by_csv_column = {}
        source = {}
        for (path, value) in by_xpath.items():

            # Finding and organizing Contributors
            if 'respStmt' in path:
                afnor_names = set([])
                for name in value.get(u'name'):
                    RE_NAME = r'(?P<first>[^\s]*)\s+(?P<last>.*)'
                    match = re.match(RE_NAME, name[1])
                    if match:
                        afnor_name = u"%s, %s" % (match.groupdict().get('last'), match.groupdict().get('first'))
                        afnor_names.add(afnor_name)
                    else:
                        logging.warning("Ignoring contributor '%s' (%s)" % (name[1], self.filePath))
                by_csv_column[path] = u' ; '.join(afnor_names)

            # Finding sources
            elif '#fileDesc#sourceDesc' == path or path == '#fileDesc#sourceDesc#bibl_target':
                for (index, info) in value.values().pop():
                    source[index] = info
            else:
                for value_key in value.keys():
                    new_path = u'%s%s' % (path, '' if value_key == 'p' else u'_%s' % value_key)
                    # import ipdb; ipdb.set_trace()
                    by_csv_column[new_path] = u' ; '.join([c[1] for c in by_xpath[path][value_key]])

        # Organizing sources:
        if source:
            by_csv_column["dcterms:source"] = u' ; '.join([source[k] for k in sorted(source.keys(), reverse=True)])

        return by_csv_column


    def metadata_to_omeka_compliant_csv(self, headers=[]):
        """
        Returns the metadata in a format which can be read by
        Omeka-s module "CSVImport".
        :return: The udated CSV header, The metadata of the current document in CSV format
        """

        omeka_metadata = self.__header_to_omeka_dict()

        # Check that the header is exhaustive
        if headers:
            missing = set(omeka_metadata.keys())-set(headers)
            headers.extend(missing)
        else:
            headers = sorted(omeka_metadata.keys())

        header_sorted_omeka_metadata = [omeka_metadata.get(h, None) for h in headers]

        return headers, header_sorted_omeka_metadata



