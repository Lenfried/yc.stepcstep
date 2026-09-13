# -*- coding: utf-8 -*-
"""Installer for the yc.stepcstep package."""
from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
])


setup(
    name='yc.stepcstep',
    version='1.0.0a1',
    description='STEP and CSTEP student application intake for York College',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: Addon',
        'Framework :: Plone :: 6.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ],
    keywords='Python Plone CMS STEP CSTEP',
    author='York College CUNY',
    url='https://github.com/rnunez80/yc.stepcstep',
    project_urls={
        'Source': 'https://github.com/rnunez80/yc.stepcstep',
        'Tracker': 'https://github.com/rnunez80/yc.stepcstep/issues',
    },
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['yc'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.9',
    install_requires=[
        'setuptools',
        'plone.api>=1.8.4',
        'plone.app.dexterity',
        'plone.schema',
        'Products.CMFPlone>=6.0',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.app.contenttypes',
            'plone.testing',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
