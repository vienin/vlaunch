# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\src\\launcher-dd.py'],
             pathex=['.'])

includes = [('settings.conf', 'settings.conf', 'BINARY'),
            ('locale/fr/LC_MESSAGES/vlaunch.mo', 'vlaunch.mo', 'BINARY'),
            ('Microsoft.VC80.CRT\\Microsoft.VC80.CRT.manifest', 'Microsoft.VC80.CRT\\Microsoft.VC80.CRT.manifest.rename', 'BINARY'),
            ('Microsoft.VC80.CRT\\msvcp80.dll', 'Microsoft.VC80.CRT\\msvcp80.dll.rename', 'BINARY'),
            ('Microsoft.VC80.CRT\\msvcr80.dll', 'Microsoft.VC80.CRT\\msvcr80.dll.rename', 'BINARY'),
            ('Microsoft.VC90.CRT\\Microsoft.VC90.CRT.manifest', 'Microsoft.VC90.CRT\\Microsoft.VC90.CRT.manifest.rename', 'BINARY'),
            ('Microsoft.VC90.CRT\\msvcp90.dll', 'Microsoft.VC90.CRT\\msvcp90.dll.rename', 'BINARY'),
            ('Microsoft.VC90.CRT\\msvcr90.dll', 'Microsoft.VC90.CRT\\msvcr90.dll.rename', 'BINARY'),
            ('Microsoft.VC90.CRT\\msvcm90.dll', 'Microsoft.VC90.CRT\\msvcm90.dll.rename', 'BINARY')
            ]

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
