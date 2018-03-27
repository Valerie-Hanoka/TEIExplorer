#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import unidecode
from unicodedata import normalize

from pylru import lrudecorator

# --- String Normalization --- #

def normalize_str(s):
    """ Remove leading and trailing and multiple whitspaces from a string s.

    :param s: a string or unicode
    :return: the unicode normalised version of s
    """
    if isinstance(s, str):
        s = unicode(s.strip(), 'utf-8')
    else:
        s = s.strip()
    s = normalize('NFC', s)
    return u' '.join(s.split())


# ---- Crappy Termhood Approximation ---- #
def is_content_word(word):
    """
    A baseline function for approximating if a word
    is a content word
    :param word:
    :return: True if word is a content word, False otherwise.
    """
    if word.isalpha():
        if len(word) > 2:
            if word.lower() not in stoplist:
                return True
    return False


# ----  Person  ---- #

ALPHA_TOKEN = re.compile('\w+', re.UNICODE)

PARTICULE_DE_RE = re.compile('\s+d[e\'][\s,$]+', re.IGNORECASE)
name_stopwords = [u'mme', u'madame', u'monsieur',
                  u'abb[ée]', u'm. de', u'comte de', u'prince']
NAME_STOPWORDS_RE = re.compile(u" +| +".join(name_stopwords), re.IGNORECASE)

@lrudecorator(100)
def get_name_initials(name):
    """
    Returns the initials of a given name.
    :param name:
    :return:
    """
    name = u" %s " % name
    name = re.sub(NAME_STOPWORDS_RE, ' ', name)
    name = re.sub(PARTICULE_DE_RE, ' ', name)
    return u''.join([
        normalize('NFD', name_part)[0].lower()
        for name_part in re.findall(ALPHA_TOKEN, name)])


PERSON_WITH_COMMA_RE = re.compile('(?P<last_name>^[^,(0-9]*),?\s*'
                                  '(?P<first_name_or_initials>[^(,]*)[^0-9]*'
                                  '(?P<birth>[0-9][0-9][0-9\.][0-9\.])?[^0-9]*'
                                  '(?P<death>[0-9][0-9][0-9\.][0-9\.])?')

PERSON_WITHOUT_COMMA_RE = re.compile('(?P<first_name_or_initials>.*\s(de)?)?\s+'
                                     '(?P<last_name>(la\s+)?[^\s]*?)',
                                     re.IGNORECASE)


def parse_person(value):
    """ Parse a person information
    :param value:
    :return:
    """
    parsed = {}
    # Case I: The name of the person has the form:
    # Name, SurnameOrInitials [(birthDate - deathDate)]
    match_person_with_comma = re.search(PERSON_WITH_COMMA_RE, value)
    if match_person_with_comma:
        parsed = match_person_with_comma.groupdict()
    else:
        # Case II: The name of the person has the form:
        # SurnameOrInitials Name  OR  Name
        match_person_without_comma = re.search(PERSON_WITHOUT_COMMA_RE, value)
        if match_person_without_comma:
            parsed = match_person_with_comma.groupdict()

    if parsed:
        # Computing the author "fingerprint" which will be used to reconcile the authors
        first_name = parsed.get('first_name_or_initials', u'')
        first_name_initials = get_name_initials(first_name) if len(first_name) > 0 else u''
        last_name = parsed.get('last_name', u'')
        last_name_normalised = filter(
            str.isalpha,
            str.lower(unidecode.unidecode(last_name))
        )

        parsed['fingerprint'] = u"%s%s" % (
            last_name_normalised,
            first_name_initials
        )
    return parsed


# ----  Date  ---- #
DATE_RE = re.compile(
    '(?P<raw_before>[A-Za-z,\- ]*)'
    '(?P<millennium>-?[0-9])'
    '(?P<century>[0-9])'
    '(?P<decade>.)'
    '(?P<year>.)'
    '(?P<raw_after>[A-Za-z,\- ]*)')

IS_NUM = re.compile('[0-9]')


def parse_year_date(value):
    """ Parse a year date
    :param value: A year date
    :return: A dictionary with millennium, century, decade, year of the date identified. -1 means no info
    """
    match = re.search(DATE_RE, value)
    parsed = {}
    if match:
        for k, v in match.groupdict().items():
            if k.startswith('raw_'):
                if v:
                    parsed[k] = v
            else:
                parsed[k] = int(v) if re.match(IS_NUM, v) else -1
        if parsed['decade'] >= 0 and parsed['year'] >= 0:
            parsed['deduced_date'] = int(
                '%i%i%i%i' %(parsed['millennium'],
                             parsed['century'],
                             parsed['decade'],
                             parsed['year']))
    return parsed


# French only atm - TODO: allow other languages
stoplist = [
    u'ai',
    u'aie',
    u'aient',
    u'aies',
    u'ait',
    u'alors',
    u'après',
    u'as',
    u'au',
    u'aucuns',
    u'aura',
    u'aurai',
    u'auraient',
    u'aurais',
    u'aurait',
    u'auras',
    u'aurez',
    u'auriez',
    u'aurions',
    u'aurons',
    u'auront',
    u'aussi',
    u'autre',
    u'aux',
    u'avaient',
    u'avais',
    u'avait',
    u'avant',
    u'avec',
    u'avez',
    u'aviez',
    u'avions',
    u'avoir',
    u'avons',
    u'ayant',
    u'ayez',
    u'ayons',
    u'bon',
    u'bons',
    u'bien',
    u'biens',
    u'c',
    u'car',
    u'ce',
    u'ceci',
    u'cela',
    u'celà',
    u'celà',
    u'ces',
    u'cet',
    u'cette',
    u'ceux',
    u'chaque',
    u'chapitre',
    u'chapitres',
    u'ci',
    u'comme',
    u'comment',
    u'd',
    u'dans',
    u'de',
    u'dedans',
    u'dehors',
    u'depuis',
    u'des',
    u'deux',
    u'devrait',
    u'doit',
    u'donc',
    u'dont',
    u'dos',
    u'droite',
    u'du',
    u'début',
    u'elle',
    u'elles',
    u'en',
    u'encore',
    u'entre',
    u'es',
    u'essai',
    u'est',
    u'estre',
    u'et',
    u'eu',
    u'eue',
    u'eues',
    u'eurent',
    u'eus',
    u'eusse',
    u'eussent',
    u'eusses',
    u'eussiez',
    u'eussions',
    u'eut',
    u'eux',
    u'eûmes',
    u'eût',
    u'eûtes',
    u'faire',
    u'fait',
    u'faites',
    u'fois',
    u'font',
    u'force',
    u'furent',
    u'fus',
    u'fusse',
    u'fussent',
    u'fusses',
    u'fussiez',
    u'fussions',
    u'fut',
    u'fûmes',
    u'fût',
    u'fûtes',
    u'haut',
    u'hors',
    u'ici',
    u'il',
    u'ils',
    u'j',
    u'je',
    u'juste',
    u'l',
    u'la',
    u'le',
    u'les',
    u'leur',
    u'leurs',
    u'lui',
    u'là',
    u'm',
    u'ma',
    u'maintenant',
    u'mais',
    u'me',
    u'mes',
    u'mine',
    u'moi',
    u'moins',
    u'mon',
    u'mot',
    u'même',
    u'n',
    u'nbsp',
    u'ne',
    u'ni',
    u'nommés',
    u'nos',
    u'notre',
    u'nous',
    u'nouveaux',
    u'on',
    u'ont',
    u'ou',
    u'où',
    u'page',
    u'pages',
    u'par',
    u'parce',
    u'parole',
    u'pas',
    u'personnes',
    u'peu',
    u'peut',
    u'pièce',
    u'plus',
    u'plupart',
    u'pour',
    u'pourquoi',
    u'qu',
    u'quand',
    u'que',
    u'quel',
    u'quelle',
    u'quelles',
    u'quels',
    u'qui',
    u's',
    u'sa',
    u'sans',
    u'se',
    u'sera',
    u'serai',
    u'seraient',
    u'serais',
    u'serait',
    u'seras',
    u'serez',
    u'seriez',
    u'serions',
    u'serons',
    u'seront',
    u'ses',
    u'seulement',
    u'si',
    u'sien',
    u'soi',
    u'soient',
    u'sois',
    u'soit',
    u'sommes',
    u'son',
    u'sont',
    u'sous',
    u'soyez',
    u'soyons',
    u'suis',
    u'sujet',
    u'sur',
    u't',
    u'ta',
    u'tandis',
    u'te',
    u'tellement',
    u'tels',
    u'tes',
    u'toi',
    u'ton',
    u'tous',
    u'tout',
    u'toute',
    u'trop',
    u'très',
    u'tu',
    u'un',
    u'une',
    u'valeur',
    u'voie',
    u'voient',
    u'vont',
    u'vos',
    u'vostre',
    u'votre',
    u'vous',
    u'vu',
    u'y',
    u'à',
    u'ça',
    u'étaient',
    u'étais',
    u'était',
    u'étant',
    u'état',
    u'étiez',
    u'étions',
    u'été',
    u'étée',
    u'étées',
    u'étés',
    u'êtes',
    u'être',
]