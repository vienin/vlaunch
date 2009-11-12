a = Analysis([os.path.join(HOMEPATH,'support', '_mountzlib.py'), os.path.join(HOMEPATH,'support', 'useUnicode.py'), '../src/launcher.py'],
             pathex=['.'])
pyz = PYZ(a.pure)

includes = [('settings.conf', 'settings.conf.livecd', 'BINARY'),
             ('UFO.svg', 'UFO.svg', 'BINARY'),
             ('UFO.png', 'UFO.png', 'BINARY'),
             ('bootdisk.vdi', 'bootdisk.vdi', 'BINARY'),
             ('ufo_swap.vdi', 'ufo_swap.vdi', 'BINARY'),
             ('ufo-generic.png', 'ufo-generic.png', 'BINARY'),
             ('ufo-generic.bmp', 'ufo-generic.bmp', 'BINARY')]

for root,dirs,files in os.walk('.\\dist\\bin'):
    for file in files:
	if file!="msvcp71.dll" and file!="msvcr71.dll":
            includes.append((file, os.path.join(root, file), 'BINARY'))

exe = EXE(pyz,
          a.scripts,
          a.binaries + includes,
          exclude_binaries=0,
          name='Live-UFO.exe',
          debug=0,
          strip=False,
          upx=False,
          console=0,
          icon='UFO.ico')
