from setuptools import setup, find_packages

setup(
    name='osm2gtfs',
    version='0.0.1',
    description='Turn OpenStreetMap data and schedule information into GTFS',
    long_description='Use public transport data from OpenStreetMap and external schedule information to create a General Transit Feed (GTFS).',
    url='https://github.com/grote/osm2gtfs',
    license='GPLv3',
    keywords='openstreetmap gtfs schedule public-transportation python',
    author='Various collaborators: https://github.com/grote/osm2gtfs/graphs/contributors',

    install_requires=['attrs', 'overpy>=0.4', 'transitfeed', 'mock', 'webcolors'],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'osm2gtfs = osm2gtfs.osm2gtfs:main'
        ]
    },
)
