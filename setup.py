from setuptools import setup

version = '0.1.8'
description = 'The GenericSuite for Python (backend version).'
long_description = '''
The GenericSuite AI
===================

GenericSuite (backend version) is a versatile backend solution, designed to
provide a comprehensive suite of features for Python APIs. It supports various
frameworks including FastAPI, Flask and Chalice, making it adaptable to a
range of projects. This repository contains the backend logic, utilities, and
configurations necessary to build and deploy scalable and maintainable
applications.
'''.lstrip()

# https://pypi.org/classifiers/

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: ISC License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    "Operating System :: OS Independent",
    'Topic :: Software Development',
]

setup(
    name='genericsuite',
    python_requires='>=3.9,<4.0',
    version=version,
    description=description,
    long_description=long_description,
    author='Carlos J. Ramirez',
    author_email='tomkat_cr@yahoo.com',
    url='https://github.com/tomkat-cr/genericsuite-be',
    license='ISC License',
    py_modules=['genericsuite'],
    classifiers=classifiers,
)
