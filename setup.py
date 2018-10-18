from setuptools import setup, find_packages


with open('README.rst') as fp:
    long_description = fp.read()

CLASSIFIERS = """
Development Status :: 3 - Alpha
Intended Audience :: Developers
Programming Language :: Python :: 3.6
Topic :: Software Development
"""

setup(
    name='kicktipper',
    version='0.9.0',
    author='',
    author_email='euphiment@gmx.de',
    url='',
    description='Interface with kicktipp.de',
    long_description=long_description,
    packages=find_packages(),
    classifiers=[f for f in CLASSIFIERS.split('\n') if f],
    install_requires=['numpy',
                      'mechanicalsoup',
                      'pandas'],
)
