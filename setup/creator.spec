# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\src\\launcher-dd.py'],
             pathex=['.'])

includes = [('settings.conf', 'settings.conf', 'BINARY'),
            ('locale/fr/LC_MESSAGES/vlaunch.mo', 'vlaunch.mo', 'BINARY')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries + includes,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'Mobile PC Creator.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False, icon='..\\graphics\\creator.ico', manifest='manifest.xml')
