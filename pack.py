
import tarfile
import sys
import os


if len(sys.argv) == 2:
    folder_to_pack = sys.argv[1]
    with tarfile.TarFile(folder_to_pack + ".tar", "w") as f:
        for i in os.listdir(folder_to_pack):
            print(os.path.join(folder_to_pack, i), "->", os.path.relpath(os.path.join(folder_to_pack, i), start=folder_to_pack))
            f.add(os.path.join(folder_to_pack, i), os.path.relpath(os.path.join(folder_to_pack, i), start=folder_to_pack))
