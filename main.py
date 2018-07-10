#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Valérie Hanoka

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

-----------------------------------------------------------
-                     PREAMBLE
-----------------------------------------------------------

When exploring a corpus of documents XML/TEI, one may need to
know what texts are similar, and on what basis.
This package intend to become a suite for XML-TEI encoded text comparison.
It will allow to:
    - Read, reconcile and store metadata information of each XML/TEI document
      e.g. :
         • Header metadata: Title, Author(s),...
         • Body metrics: #words, #sentences, polarity, ...
    - Run an unsupervised comparing tool for a set of texts (To be done).

This tool is being developed as part of the OBVIL projects.

"""

import os
import sys
import glob
import logging
import time
import json
import unicodecsv
from optparse import OptionParser
from teiexplorer.corpusreader import tei_content_scraper as tcscraper
from teiexplorer.utils.sqlite_basic import (
    CorpusSQLiteDBWriter,
    CorpusSQLiteDBReader
)

# import metadataGraph as mdg

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO)


def tei_to_omeka_header(header):
    """ Transforms an XML-TEI header path to a Omeka-s (semantic-web compliant) header."""


    # XML-TEI headers elements to Linked Data correspondences
    xml_tag_to_voc = {
        u"#fileDesc#titleStmt_title": u"dcterms:title",
        u"#fileDesc#titleStmt_author_key": u"dcterms:creator",
        u"#fileDesc#titleStmt_author": u"dcterms:creator",
        u"#fileDesc#editionStmt#respStmt": u"dcterms:contributor",
        u"#fileDesc#publicationStmt_publisher": u"dcterms:publisher",
        u"#profileDesc#creation_when": u"dcterms:date",
        u"#profileDesc#langUsage_ident": u"dcterms:language",
        u"#fileDesc#publicationStmt_idno": u"dcterms:identifier",  # Mandatory for Gallica
        u"#fileDesc#titleStmt_editor_key": u"http://schema.org/editor",
        u'#fileDesc#publicationStmt#availability#licence': u"dcterms:rights",
        u"#fileDesc#publicationStmt#availability#licence_": u"dcterms:rights",
        u"#fileDesc#publicationStmt#licence": u"dcterms:rights",
    }

    if xml_tag_to_voc.get(header, None):
        return xml_tag_to_voc.get(header, header)

    if u'#fileDesc#editionStmt#respStmt_' in header:
        return u"dcterms:contributor"

    return header

def parse_tei_documents(corpora, database=None, omeka_csv_folder=None):
    """
    Extracting metadata from all the documents in corpora.
    Optionally saving this information in a SQLite database.
    :param corpora: Corpora locations where TEI files are stored
    :param database: The database where the metadata should be stored. If none, no storage.
    :param csv_file: The file where the transformed metadata information in
                     Omeka-s CSVimport format should be written.
    :return:
    """

    if omeka_csv_folder:

        # Creating the folder if it does not exists
        if not os.path.exists(omeka_csv_folder):
            os.makedirs(omeka_csv_folder)



    # The 'corpus_tag' corresponds to a label giving a hint on the corpus provenance.
    for (corpus_tag, corpus_location) in corpora.items():

        csv_header_info = []
        csv_matadata_list = []

        test_limit = 0
        for document_file in glob.glob(corpus_location):
            if debug_size and test_limit >= debug_size:
                continue
            test_limit += 1
            logging.info(u"Parsing %s" % document_file)
            document = tcscraper.TeiContent(document_file, corpus_tag)

            # Doing clustering on content.
            # if document.metadata:
            # corpus.add_metadata(document_file, document.metadata)
            # corpus.add_text_content(document_file,document.content_words)

            # Adding the metadata information to the document
            if database:
                database.add_xml_document(document)

            if omeka_csv_folder:
                csv_header_info, csv_metadata = document.metadata_to_omeka_compliant_csv(csv_header_info)
                csv_metadata.insert(0, "text/xml")
                csv_matadata_list.append(csv_metadata)
            del document

        if omeka_csv_folder:
            csv_file = u'%s/%s.csv' % (omeka_csv_folder, corpus_tag)
            csv_f = open(csv_file, 'wb')
            csv_writer = unicodecsv.writer(csv_f, encoding='utf-8')
            csv_header_info = [tei_to_omeka_header(h) for h in csv_header_info]
            csv_header_info.insert(0, u"dcterms:format")
            csv_writer.writerow(csv_header_info)
            csv_writer.writerows(csv_matadata_list)
            csv_f.close()


if __name__ == "__main__":

    usage = """usage: ./%prog [--parse]
    • parse TEI documents and save result in DB metadata.db: 
      python3 main.py -c configs/config.json -p -s -d metadata.db
    • use a previously computed metadata DB metadata.db to save the transformed
      metadata information in the header of a new document:
      python3 main.py -c configs/config.json -a -d metadata.db
    • Save a simplified version of the metadata DB to a CSV file:
      python3 main.py -d metadata.db [-y path/to/dewey/corresp/file.tsv] -v newCSVsimplifiedDB.csv
    • Export all the corpus to Omeka via CSV file
      python3 main.py  -c configs/config_omeka.json -p -o omeka

    """
    parser = OptionParser(usage)
    parser.add_option("-c", "--config",
                      dest="config_file",
                      help="The configuration file to use. See the template config.json.")
    parser.add_option("-p", "--parse",
                      action="store_true", dest="parse_tei", default=False,
                      help="Will parse xml/tei whose paths are provided."
                      )
    parser.add_option("-d", "--database",
                      dest="database",
                      help="The database where the corpus info are/should be stored.")

    parser.add_option("-s", "--saveToDatabase",
                      action="store_true",
                      dest="save_to_database",
                      default=False,
                      help="Saves the corpus info in a database.")

    parser.add_option("-v", "--saveDatabaseToCSVFile",
                      dest="db_csv_file",
                      default=False,
                      help="Saves the main database information in a CSV format.")

    parser.add_option("-a", "--amendTEIdocument",
                      action="store_true",
                      dest="amend_TEI",
                      default=False,
                      help="Saves the transformed metadata information in the TEI header.")

    parser.add_option("-o", "--omekaCSVImportFolder",
                      dest="omeka_csv_folder",
                      default=False,
                      help="Name of the folder in which the file where the transformed metadata information in "
                           "an Omeka-s CSVimport format should be written.")

    parser.add_option("-y", "--deweyFilePath",
                      dest="dewey_filepath",
                      default=False,
                      help="Name of the Dewey/Document-ark correspondences file path.")

    (options, args) = parser.parse_args()

    if options.config_file:
        with open(options.config_file) as jsonfile:
            config = json.load(jsonfile)
            debug_size = config.get("debug_size", None)
            corpora = config["corpora"]

    # Results will be saved or read from a SQLite Database
    db_name = 'UseAndReuse_%s.sqlite' % time.strftime('%b_%d_%Y_%H:%M:%S')
    if options.database:
        db_name = options.database

    # -- Parse the corpus and optionally save it (in DB of Omeka CSV mass import format-- #
    if options.parse_tei:
        db = CorpusSQLiteDBWriter(db_name) if options.save_to_database else None
        parse_tei_documents(corpora, database=db, omeka_csv_folder=options.omeka_csv_folder)

    # -- Modify corpus's TEI content -- #
    if options.amend_TEI and options.database:
        db = CorpusSQLiteDBReader(db_name)
        db.treat_document(modify_TEI=False, dewey_filepath=options.dewey_filepath)

    # -- Export the main information of the DB in CSV format
    if options.db_csv_file and options.database:
        db = CorpusSQLiteDBReader(db_name)
        db.export_to_csv(options.db_csv_file, dewey_filepath=options.dewey_filepath)

    sys.exit()
