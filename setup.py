from setuptools import setup, find_packages

setup(
    name='osm2gtfs',
    install_requires=['overpy>=0.4', 'transitfeed'],
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
        [console_scripts]
        osm2gtfs = osm2gtfs.osm2gtfs:main
    '''
)
