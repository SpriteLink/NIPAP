from setuptools import setup, find_packages

setup(
    name='nipap-www',
    version='0.5.0',
    description='web frontend for NIPAP',
    author='Kristian Larsson, Lukas Garberg',
    author_email='kll@tele2.net, lukas@spritelink.net',
    url='https://github.com/plajjan/NIPAP',
    install_requires=[
        "Pylons>=1.0",
        "Jinja2",
        "pynipap",
        "nipapd"
    ],
#    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'nipapwww': ['i18n/*/LC_MESSAGES/*.mo']},
    data_files = [
        ( '/etc/nipap/', [ 'nipap-www.ini' ] ),
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
