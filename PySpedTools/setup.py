# coding=utf-8
from setuptools import setup, find_packages

setup(
    name="PySpedTools",
    version="0.1",
    author="Danimar Ribeiro",
    author_email='danimaribeiro@gmail.com',
    keywords=['nfe', 'nfse'],
    classifiers=[
        'Development Status :: 1 - alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or \
        later (LGPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(exclude=['*test*']),
    package_data={'pysped_tools': ['schema/*xsd']},
    license='LGPL-v2.1+',
    description='PySpedTools é uma biblioteca para envio de NFe',
    long_description='PySpedTools'
)
