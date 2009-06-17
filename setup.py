from distutils.core import setup
import py2exe
import sys
import glob

def files(folder):
    for path in glob.glob(folder+'/*'):
        if os.path.isfile(path):
            yield path

data_files=[
            ('.', glob.glob(sys.prefix+'/DLLs/tix85*.dll')),
            ('tcl/tix8.5', files(sys.prefix+'/tcl/tix8.5')),
            ('tcl/tix8.5/bitmaps', files(sys.prefix+'/tcl/tix8.5/bitmaps')),
            ('tcl/tix8.5/pref', files(sys.prefix+'/tcl/tix8.5/pref')),
           ]

setup(zipfile = None,
      #options = {'py2exe': {'bundle_files': 1}},
      windows = [{'script': "launcher.py", "icon_resources" : [(1, "UFO.ico")]}],
      
      data_files=data_files,
)
