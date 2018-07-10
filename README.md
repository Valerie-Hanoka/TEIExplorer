![TEIExplorer](https://github.com/Valerie-Hanoka/TEIExplorer/blob/master/illustration.png)

A tool to explore and compare OBVIL XML/TEI French Litterature Corpora
========================================================================================

This package provides an XML-TEI parser for OBVIL corpora.
With it, you can read and store metadata information for 
each XML/TEI document (Title, Author(s), dates, ...) and normalize the metadata.

This tool is being developed as part of the OBVIL projects.
See http://obvil.paris-sorbonne.fr/

#### Usage

* Parse TEI documents and save result in DB metadata.db:
 ``python3 main.py -c configs/config.json -p -s -d metadata.db``
 
 The structure of the resulting DB is: 
 
![db schema](https://github.com/Valerie-Hanoka/TEIExplorer/blob/master/TEIExplorerMdDb.png)
 

* Use a previously computed metadata DB metadata.db to save the transformed
   metadata information in the header of a new document:   
 ``python3 main.py -c configs/config.json -a -d metadata.db``

   Meta-data are filtered, reconciled and put back in the XML-TEI in an `xenoData` élément:
```html
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Oeuvres de P. de Ronsard,...</title>
        <author role="Auteur du texte" key="11922538">Ronsard, Pierre de (1524-1585)</author>
        <respStmt>
          <resp key="360">Éditeur scientifique</resp>
          <name key="12325002">Marty-Laveaux, Charles (1823-1899)</name>
        </respStmt>
      </titleStmt>
      <publicationStmt>
        <publisher>TGB (BnF – OBVIL)</publisher>
      </publicationStmt>
      <seriesStmt>
        <title level="s">Oeuvres de P. de Ronsard,...</title>
        <title level="a">Tome 4</title>
        <biblScope unit="volumes" n="5"/>
        <idno>cb30899400w</idno>
      </seriesStmt>
      <sourceDesc>
        <bibl>
          <idno>http://gallica.bnf.fr/ark:/12148/bpt6k5424157w</idno>
          <publisher>A. Lemerre</publisher>
          <date when="1887">1887-1893</date>
        </bibl>
      </sourceDesc>
    </fileDesc>
    <xenoData>
      <date>1887</date>
      <title>Oeuvres de P. de Ronsard,... — Tome 4</title>
      <dewey>840 - Littératures des langues romanes. Littérature française</dewey>
      <meta-data_comprehensiveness_score>0.67</meta-data_comprehensiveness_score>
      <authors>
        <author_1>
          <alpha_key>ronsardp</alpha_key>
          <age_at_publication>363</age_at_publication>
          <last_name>Ronsard</last_name>
          <author>Ronsard, Pierre de, 1524-1585.</author>
          <first_name_or_initials>Pierre de</first_name_or_initials>
          <is_reconciliated>True</is_reconciliated>
          <death>1585</death>
          <role>Auteur du texte</role>
          <birth>1524</birth>
        </author_1>
      </authors>
    </xenoData>
  </teiHeader>
```

* Save a simplified version of the metadata DB to a CSV file:
 ``python3 main.py -d metadata.db [-y path/to/dewey/corresp/file.tsv] -v newCSVsimplifiedDB.csv``

* Export all the corpus to Omeka via CSV file
 ``python3 main.py  -c configs/config_omeka.json -p -o omeka`

---------------
