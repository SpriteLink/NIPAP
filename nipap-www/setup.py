from setuptools import setup, find_packages
import re
import nipapwww

with open('requirements.txt', 'r') as f:
    requires = [re.sub(r'\s*([\w_\-\.\d]+([<>=]+\S+|)).*', r'\1', x.strip())
                for x in f if
                x.strip() and re.match(r'^\s*\w+', x.strip())]

setup(
    name='nipap-www',
    version=nipapwww.__version__,
    description='web frontend for NIPAP',
    author=nipapwww.__author__,
    author_email=nipapwww.__author_email__,
    url=nipapwww.__url__,
    install_requires=requires,
    license=nipapwww.__license__,
#    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'nipapwww': ['i18n/*/LC_MESSAGES/*.mo']},
    data_files = [
        ( '/etc/nipap/', [ 'nipap-www.ini', ] ),
        ( '/etc/nipap/www', [ 'nipap-www.wsgi', ] ),
        ( '/var/cache/nipap-www/', [] )
    ],
    #message_extractors={'nipapwww': [
    #        ('**.py', 'python', None),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
#    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = nipapwww.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
