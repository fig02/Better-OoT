# -*- mode: python -*-

block_cipher = None


a = Analysis(['../Gui.py'],
             pathex=['E:\\Better-OoT'],
             binaries=[],
             datas=[('../data/', 'data'), ('../bin/', 'bin')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['lzma', 'bz2'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='BetterOoT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True, 
          icon='E:\\Better-OoT\\data\\er.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='BetterOoT')
