from setuptools import setup, find_packages
from glob import glob
from os.path import basename, splitext

setup(
    name='zimport',
    version='0.1.0',
    description='zimport is used to load and manage python packages from zip-archives.',
    url='https://github.com/waveware4ai/zimport',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    license='GPL-3.0 license',
    author='14mhz',
    author_email='14mhz@hanmail.net',
    keywords='python import package zip pyd',
    python_requires='>=3.8',   
    packages=['zimport','zimport.util'],
)
