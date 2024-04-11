from setuptools import find_packages, setup

import nipapwww

setup(
    name='nipap-www',
    version=nipapwww.__version__,
    description='web frontend for NIPAP',
    author=nipapwww.__author__,
    author_email=nipapwww.__author_email__,
    url=nipapwww.__url__,
    install_requires=[
        "Flask",
        "pynipap",
        "nipap"
    ],
    license=nipapwww.__license__,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    package_data={'nipapwww': ['i18n/*/LC_MESSAGES/*.mo']},
    data_files=[
        ('/etc/nipap/www', ['nipap-www.wsgi', ]),
    ],
    zip_safe=False,
)
