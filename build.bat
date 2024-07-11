nuitka --windows-icon-from-ico=icon.ico --onefile main.py
rd main.build /s/q
del main.cmd
mv main.exe sppite.exe