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
This package intend to become a suite for text comparison.
It will allow to:
    - Read and store metadata information of each XML/TEI document
      e.g. :
         • Header metadata: Title, Author(s),...
         • Body metrics: #words, #sentences, polarity, ...
    - Run an unsupervised comparing tool for a set of texts (To be done).

This tool is being developed as part of the OBVIL projects.
See http://obvil.paris-sorbonne.fr/

For the moment, it is dirty and can't be used. Sorry.
"""

import sys
import glob
import logging
import time
import json
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


def parse_tei_documents(corpora, database):
    """
    Extracting metadata from all the documents in corpora.
    Optionally saving this information in a SQLite database.
    :param corpora: Corpora locations where TEI files are stored
    :param database: The database where tmetadata should be stored. If none, no storage.
    :return:
    """
    # The 'corpus_tag' corresponds to a label giving a hint on the corpus provenance.
    for (corpus_tag, corpus_location) in corpora.items():
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

            del document


if __name__ == "__main__":

    usage = """usage: ./%prog [--parse]
    • parse TEI documents and save result in DB useAndReuse.db: 
      python main.py -c configs/config.json -p -s -d metadata.db
    • use a previously computed metadata DB metadata.db to save the transformed
      metadata information in the header of a new document:
      python main.py -c configs/config.json -a -d useAndReuse.db

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

    parser.add_option("-a", "--amendTEIdocument",
                      action="store_true",
                      dest="amend_TEI",
                      default=False,
                      help="Saves the transformed metadata information in the TEI header.")

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

    # -- Parse the corpus and optionally save it -- #
    if options.parse_tei:
        db = CorpusSQLiteDBWriter(db_name) if options.save_to_database else None
        parse_tei_documents(corpora, db)

    # -- Modify corpus's TEI content -- #
    if options.amend_TEI:
        db = CorpusSQLiteDBReader(db_name)
        db.treat_document(dewey_filepath='data/databases/dewey_corresp_utf8.tsv')



    # # save_to_format(corpus.get_metadata_list(), options.output_filename, options.format)
    # corpus.cluster(options.output_filename)
    #
    # clusters_info = corpus.clustering_result
    # for cluster_id in clusters_info.keys():
    #     save_to_format(
    #         corpus.clustering_result[cluster_id],
    #         "%s_cluster_%i" % (options.output_filename, cluster_id), "json")

    # Building objects to keep all information about metadata. Put that before the rest.
    # corpus = CorpusComparer()

    sys.exit()









##########################################
#     Temporary: Saving Results          #
##########################################
# def save_to_json(data, json_output_filename):
#     """Saves a Python data structure in a JSON file output_filename.
#     :param data:
#     :param json_output_filename:
#     """
#     with codecs.open(json_output_filename, 'w', encoding="utf-8") as file:
#         json.dump(data, file, ensure_ascii=False)
#         # import ipdb; ipdb.set_trace()
#         logging.info(u"Dumped in %s" % json_output_filename)
#
#
# def save_to_format(data, output_filename, file_format):
#     """This function saves the current data
#     in the specified file_format usinf the file name output_filname.
#     If the file_format is not specified or not supported, the data is
#     saved in a json format.
#     :param data:
#     :param output_filename:
#     :param file_format:
#     """
#     output_filename = output_filename if output_filename else "output_"+time.strftime('%a_%H_%M')
#     file_format = file_format if file_format else ""
#     result_file = output_filename + "." + file_format
#
#     if file_format == 'json':
#         save_to_json(data, 'data/results/%s' % result_file)
#         logging.info(u"Saved in %s" % result_file)
#     else:
#         save_to_json(data, 'data/results/%s' % result_file + "json")
#         logging.info(u"Saved in %sjson" % result_file)


sum([20,14,14,13,13,13,13,12,12,12,11,11,11,10,10,10,10,9,9,9,9,9,9,9,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6])
