from setuptools import setup

NAME = 'ufo'
VERSION = '1.0'

plist = dict(
    CFBundleIconFile=NAME
)

APP = [ "UFO.py" ]
# dict(script = 'UFO.py', plist = plist) ]
#APP = [ 'launcher.py', 'mac.py' ]
DATA_FILES = [ ]
OPTIONS = {'argv_emulation' : False, 'iconfile' : 'ufo.icns' }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
