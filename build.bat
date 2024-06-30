nuitka --windows-icon-from-ico=icon.ico main.py
rd main.build /s/q
del main.cmd
mv main.exe sppite.exe