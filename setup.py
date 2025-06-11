from setuptools import setup, find_packages

setup(
    name='zimport',
    version='0.1.10',
    author='14mhz',
    author_email='14mhz@hanmail.net',    
    description='zimport is used to load and manage python packages from zip-archives.',
    keywords='python import package zip pyd',
    url='https://github.com/waveware4ai/zimport',
    long_description=open('README.md', 'r', encoding='UTF8').read(),
    long_description_content_type='text/markdown',
    license='Apache-2.0 license',
    python_requires='>=3.8',   
    packages=['zimport','zimport.util'],
)

