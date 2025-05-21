from setuptools import setup, find_packages

setup(
    author='14mhz',
    author_email='14mhz@hanmail.net',
    name='zimport',
    version='0.1.0',
    description='zimport is used to load and manage python packages from zip-archives.',
    keywords='python import package zip pyd',
    url='https://github.com/waveware4ai/zimport',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    license='GPL-3.0 license',
    python_requires='>=3.8',    
)
