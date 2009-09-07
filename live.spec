import sys

name = "live"

if sys.platform == "win32":
    name += ".exe"

a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'), os.path.join(HOMEPATH,'support/useUnicode.py'), 'launcher.py'],
             pathex=['/home/bob/dev/chicoutimi/trunk/vlaunch'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries + [('settings.conf', 'settings.conf.livecd', 'BINARY')],
          name=name,
          debug=False,
          strip=False,
          upx=False,
          console=0 )
