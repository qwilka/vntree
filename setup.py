


# https://github.com/pypa/sampleproject/blob/master/setup.py

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vntree',
    version='0.1.0',
    description='A simple tree data structure in Python.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/qwilka/vn-tree',
    author='Stephen McEntee',
    author_email='stephenmce@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Natural Language :: English',
    ],
    keywords='tree data structure node',
    packages=find_packages(exclude=['docs']),
    python_requires='>=3.6',
)
