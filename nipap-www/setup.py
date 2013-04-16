from setuptools import setup, find_packages
import nipapwww

setup(
    name='nipap-www',
    version=nipapwww.__version__,
    description='web frontend for NIPAP',
    author=nipapwww.__author__,
    author_email=nipapwww.__author_email__,
    url=nipapwww.__url__,
    install_requires=[
        "Pylons>=1.0",
        "Jinja2",
        "pynipap",
        "nipap"
    ],
    license=nipapwww.__license__,
#    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'nipapwww': ['i18n/*/LC_MESSAGES/*.mo']},
    data_files = [
        ( '/etc/nipap/', [ 'nipap-www.ini', 'nipap-www.wsgi' ] ),
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
