#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
# from util import summ_dicts, create_dir
import numpy as np
import pandas as pd
# import nltk
# import re
# import os
# import codecs
# from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.externals import joblib

# import os  # for os.path.basename
from sklearn.manifold import MDS
# from scipy.cluster.hierarchy import ward, dendrogram

import seaborn as sns
import matplotlib.pyplot as plt
# import matplotlib as mpl
# import mpld3

# TODO: clean and optimized version

class CorpusComparer(object):
    """A toy class to compare documents in a corpus.
    TODO
    """

    logging.basicConfig(
            format='%(asctime)s : %(levelname)s : %(message)s',
            level=logging.INFO)

    #########################
    #  Data pre-processing
    #########################
    max_file_id = 0
    metadata = {}
    normalized_texts_files_id = {}
    normalized_texts = []
    MIN_FREQ_THRESHOLD = 1

    # Classification
    K_MEAN_CLUSTERS_NUM = 5
    CENTROID_DISPLAY_WORDS = 6
    tfidf_matrix = []
    tfidf_vectorizer = None
    dist = None

    clustering_result = {}

    def add_metadata(self, filename, metadata):
        self.metadata[filename] = metadata

    def add_text_content(self, filename, text):
        if text:
            file_index = self.normalized_texts_files_id.get(
                filename,
                len(self.normalized_texts))

            if file_index == -1:
                self.normalized_texts_files_id[filename] = self.max_file_id
                self.max_file_id += 1
                self.normalized_texts.append(text)
            else:
                # TODO _ Log an issue here
                self.normalized_texts_files_id[filename] = file_index
                self.normalized_texts.insert(file_index, text)

    def _get_text_tokens(self, document):
        # TODO - stemming or else. Chose where to normalize
        return document

    def get_metadata_list(self):
        return self.metadata.values()

    ############################################
    #       Unsupervised classification. 
    # Cf. # http://brandonrose.org/clustering
    ############################################
    def get_document_attributes(self, corresp, attr):
        return [self.metadata[f].get(attr, 'UNKN') for (f, i) in corresp]

    def get_document_aggregated_info(self, corresp):
        info_list = []
        for (f, i) in corresp:
            info = "%s %s %s %s" % (\
                   self.metadata[f].get(u'title', 'UNKN'),
                   self.metadata[f].get(u'author', 'UNKN'),
                   self.metadata[f].get(u'date', 'UNKN'),
                   self.metadata[f].get(u'_tag', 'UNKN'),
            )
            info_list.append(info)
        return info_list

    def k_means_clustering(self, filename):
        # define vectorizer parameters

        logging.info("Doing k-mean clustering")

        self.tfidf_vectorizer = TfidfVectorizer(
            max_df=0.8,
            max_features=200000,
            min_df=0.2,
            tokenizer=self._get_text_tokens,
            ngram_range=(1, 3),
            lowercase = False
        )

        # fit the vectorizer to the whole corpus
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.normalized_texts)

        km = KMeans(n_clusters=self.K_MEAN_CLUSTERS_NUM)
        km.fit(self.tfidf_matrix)
        joblib.dump(km, 'data/results/%s_cluster.pkl' % filename)
        logging.info("K-mean clustering model pickled in data/results/%s_cluster.pkl" %filename)

    def multidimensional_scaling(self):

        logging.info("Doing MDS")

        # Multidimensional scaling
        MDS()

        # convert two components as we're plotting points in a two-dimensional plane
        # "precomputed" because we provide a distance matrix
        # we will also specify `random_state` so the plot is reproducible.
        self.dist = 1 - cosine_similarity(self.tfidf_matrix)
        mds = MDS(n_components=2, dissimilarity="precomputed", random_state=1)
        pos = mds.fit_transform(self.dist)  # shape (n_components, n_samples)

        xs, ys = pos[:, 0], pos[:, 1]

        return xs, ys

    def document_clusters(self, filename):
        logging.info("Organising clusters info")

        km = joblib.load('data/results/%s_cluster.pkl' % filename)
        clusters = km.labels_.tolist()
        sorted_files_id_corresp = sorted(
            self.normalized_texts_files_id.items(), key=lambda x: x[1]
        )

        documents = {
            'title': self.get_document_attributes(sorted_files_id_corresp, u'title'),
            'file': [f for (f, i) in sorted_files_id_corresp],
            'label': self.get_document_attributes(sorted_files_id_corresp, u'LOCAL_corpus_tag'),
            'cluster': clusters,
            'author': self.get_document_attributes(sorted_files_id_corresp, u'author'),
            'year':  self.get_document_attributes(sorted_files_id_corresp, u'date'),

        }

        frame = pd.DataFrame(
            documents,
            index=[clusters],
            columns=['file', 'title', 'label', 'author', 'year', 'cluster']
        )

        terms = self.tfidf_vectorizer.get_feature_names()

        # sort cluster centers by proximity to centroid
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]

        for cluster_id in range(self.K_MEAN_CLUSTERS_NUM):
            logging.debug("\n\n--- Cluster %d --- " % cluster_id)
            cluster_name = ''
            terms_index = order_centroids[cluster_id, :self.CENTROID_DISPLAY_WORDS]
            for ind in terms_index:
                cluster_name = "%s + %s" % (cluster_name, terms[ind])
            logging.debug(cluster_name)

            cluster_name = "%i %s" %(cluster_id, cluster_name)
            logging.debug("\n--- Documents of cluster %d ---" % cluster_id)

            clusters_documents = frame.ix[cluster_id][u'file']
            if type(clusters_documents) is str:
                logging.debug(clusters_documents)
                self.metadata[clusters_documents][u'_clust'] = cluster_name
                try:
                    self.clustering_result[cluster_id].append(self.metadata[clusters_documents])
                except KeyError:
                    self.clustering_result[cluster_id] = [self.metadata[clusters_documents]]
            else:
                for document in clusters_documents.values:
                    logging.debug(document)
                    self.metadata[document][u'_clust'] = cluster_name
                    try:
                        self.clustering_result[cluster_id].append(self.metadata[document])
                    except KeyError:
                        self.clustering_result[cluster_id] = [self.metadata[document]]

    def draw_clusters(self, filename):

        logging.info("Drawing clusters")

        km = joblib.load('data/results/%s_cluster.pkl' % filename)
        clusters = km.labels_.tolist()
        sorted_files_id_corresp = sorted(
            self.normalized_texts_files_id.items(), key=lambda x: x[1]
        )

        documents = {
            'file': [f for (f, i) in sorted_files_id_corresp],
            'cluster': clusters,
            'title2': self.get_document_aggregated_info(sorted_files_id_corresp)
        }

        frame = pd.DataFrame(
            documents,
            index=[clusters],
            columns=['file', 'title2', 'cluster']
            )

        terms = self.tfidf_vectorizer.get_feature_names()
        # total_vocab = [item for sublist in self.normalized_texts for item in sublist]
        # vocab_frame = pd.DataFrame({'words': total_vocab})

        logging.info("Top terms per cluster:\n")
        # sort cluster centers by proximity to centroid
        order_centroids = km.cluster_centers_.argsort()[:, ::-1] 

        cluster_names = {}

        for cluster_id in range(self.K_MEAN_CLUSTERS_NUM):
            logging.info("\n\n--- Cluster %d --- " % cluster_id)
            cluster_name = ''
            terms_index = order_centroids[cluster_id, :self.CENTROID_DISPLAY_WORDS]
            for ind in terms_index:
                cluster_name = "%s + %s" % (cluster_name, terms[ind])
            
            cluster_names[cluster_id] = cluster_name
            logging.info(cluster_name)
            logging.info("\n--- Documents of cluster %d ---" % cluster_id)
            for document in frame.ix[cluster_id].values.tolist():
                logging.info(document)

        # Visualisation
        palette = sns.color_palette("colorblind", self.K_MEAN_CLUSTERS_NUM)
        cluster_colors = {k: v for k, v in enumerate(palette)}

        xs, ys = self.multidimensional_scaling()

        # create data frame that has the result of the MDS plus the cluster numbers and titles
        df = pd.DataFrame(dict(x=xs, y=ys, label=clusters, title=documents["title2"]))

        # group by cluster
        groups = df.groupby('label')

        # set up plot
        fig, ax = plt.subplots(figsize=(17, 9)) # set size
        ax.margins(0.5) # Optional, just adds 5% padding to the autoscaling

        # iterate through groups to layer the plot
        # note that I use the cluster_name and cluster_color dicts
        # with the 'name' lookup to return the appropriate color/label
        for name, group in groups:
            ax.plot(group.x, group.y, marker='o', linestyle='', ms=12,
                    label=cluster_names[name], color=cluster_colors[name],
                    mec='none')
            ax.set_aspect('auto')
            ax.tick_params(
                axis='x',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                bottom='off',      # ticks along the bottom edge are off
                top='off',         # ticks along the top edge are off
                labelbottom='off')
            ax.tick_params(
                axis='y',         # changes apply to the y-axis
                which='both',      # both major and minor ticks are affected
                left='off',      # ticks along the bottom edge are off
                top='off',         # ticks along the top edge are off
                labelleft='off')

        lgd = ax.legend(
            numpoints=1,
            bbox_to_anchor=(0.5, -0.1),
            loc='upper center',
            ncol=1)  # show legend with only 1 point

        # add label in x,y position with the label as the film title
        for i in range(len(df)):
            ax.text(df.ix[i]['x'], df.ix[i]['y'], df.ix[i]['title'], size=8)

        plt.savefig(
            'data/results/%s_clusters.png' % filename,
            dpi=200,
            bbox_extra_artists=(lgd,),
            bbox_inches='tight'
        )
        plt.close()

        logging.info("K-mean clusters visualisation pickled in data/results/%s_clusters.png" % filename)

        # linkage_matrix = ward(self.dist) # define the linkage_matrix using ward clustering pre-computed distances
        #
        # fig, ax = plt.subplots(figsize=(150, 200)) # set size
        # ax = dendrogram(linkage_matrix, orientation="right", labels=documents["title"]);
        #
        # plt.tick_params(\
        #     axis= 'x',          # changes apply to the x-axis
        #     which='both',      # both major and minor ticks are affected
        #     bottom='off',      # ticks along the bottom edge are off
        #     top='off',         # ticks along the top edge are off
        #     labelbottom='off')
        #
        # plt.tight_layout()  # show plot with tight layout
        #
        # # uncomment below to save figure
        # plt.savefig('data/results/%s_dendogram.png' % filename, dpi=200)  # save figure as ward_clusters
        #
        # # import ipdb; ipdb.set_trace()

    def cluster(self, run_filename):
        self.k_means_clustering(run_filename)
        self.document_clusters(run_filename)
        self.draw_clusters(run_filename)
