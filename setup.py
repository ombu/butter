"""
see http://guide.python-distribute.org/creation.html
"""

from distutils.core import setup

setup(
    name='Butter',
    version='0.0.2',
    author='OMBU',
    author_email='martin@ombuweb.com',
    packages=['butter'],
    url='https://github.com/ombu/butter',
    license='LICENSE.txt',
    description='Fabric library for developing and deploying Drupal sites.',
    long_description=open('README.rst').read(),
    install_requires=[
        "Fabric < 2.0",
        "awscli >= 1.1.0"
    ],
)
