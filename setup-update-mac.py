from setuptools import setup

NAME = 'update-launcher'
VERSION = '1.0'

plist = dict(
    CFBundleIconFile=NAME
)

APP = [ "ufo-updater.py" ]
DATA_FILES = [ ]
OPTIONS = {'argv_emulation' : False }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
