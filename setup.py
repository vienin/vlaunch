from distutils.core import setup
import py2exe
from py2exe.build_exe import py2exe as BuildExe
import os, sys
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

def TixInfo():
    import Tkinter
    import _tkinter
    
    tk=_tkinter.create()
   
    tcl_version=_tkinter.TCL_VERSION
    tk_version=_tkinter.TK_VERSION
    tix_version=tk.call("package","version","Tix")
  
    tcl_dir=tk.call("info","library")
          
    del tk, _tkinter, Tkinter
    
    return (tcl_version,tk_version,tix_version,tcl_dir)

class myPy2Exe(BuildExe):
    
    def plat_finalize(self, modules, py_files, extensions, dlls):
        BuildExe.plat_finalize(self, modules, py_files, extensions, dlls)
        
        if "Tix" in modules:
            # Tix adjustments
            tcl_version,tk_version,tix_version,tcl_dir = TixInfo()
            
            tixdll="tix%s.dll"% (tix_version.replace(".",""))
            tcldll="tcl%s.dll"%tcl_version.replace(".","")
            tkdll="tk%s.dll"%tk_version.replace(".","")

            dlls.add(os.path.join(sys.prefix,"DLLs",tixdll))
            
            self.dlls_in_exedir.extend( [tcldll,tkdll,tixdll ] )

            tcl_src_dir = os.path.split(tcl_dir)[0]
            tcl_dst_dir = os.path.join(self.lib_dir, "tcl")
            self.announce("Copying TIX files from %s..." % tcl_src_dir)
            self.copy_tree(os.path.join(tcl_src_dir, "tix%s" % tix_version),
                           os.path.join(tcl_dst_dir, "tix%s" % tix_version))


setup(zipfile = None,
      options = {'py2exe': {'bundle_files': 1}},
      windows = [{'script': "ufo.py", "icon_resources" : [(1, "UFO.ico")]}],
      cmdclass={'py2exe':myPy2Exe},
      data_files=data_files,
)
