# -*- mode: python -*-

block_cipher = None


a = Analysis(['../BetterOoT.py'],
             pathex=['E:\\Better-OoT'],
             binaries=[],
             datas=[('../data/', 'data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          name='Better OoT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True, 
          icon='E:\\Better-OoT\\data\\er.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Better OoT')
