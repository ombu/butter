from distutils.core import setup

setup(
    name='Butter',
    version='0.0.1',
    author='OMBU',
    author_email='martin@ombuweb.com',
    packages=['butter'],
    # scripts=['bin/stowe-towels.py','bin/wash-towels.py'],
    # url='http://pypi.python.org/pypi/TowelStuff/',
    license='LICENSE.txt',
    description='Fabric library for developing and deploying Drupal sites.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Fabric >= l.3.4",
    ],
)
