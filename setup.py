# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.install import install as _install


class Install(_install):
    def run(self):
        _install.do_egg_install(self)
        import nltk
        nltk.download("punkt")

setup(
    name='TEI Explorer',
    version='0.1',
    description='A toy toy to to around with XML/TEI corpora',
    url='',
    author='Valérie Hanoka',
    author_email='',
    license='MIT',
    packages=['teiexplorer'],
    cmdclass={'install': Install},
    install_requires=[
        'textblob',
        'pandas',
        'sklearn',
        'mpld3',
        'jinja2',
        'nltk',
        'sqlalchemy',
        'lxml'
    ],
    setup_requires=['nltk'],
    zip_safe=False)
