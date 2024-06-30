
# welcome! do not try to understand this code, cause neither do i...
# made by aciddev_
# licensed under WTFPL

import os
import io
import lzma
import json
import shutil
import tarfile
import requests
import subprocess

DL_CHUNK_SIZE = 65536

def log(string=""):
    print(f'[i] {string}')

def ask(string=""):
    return input(f"[?] {string}")

def download_file(url, callback=None):
    request = requests.get(url, stream=True)
    if not request.ok:
        return None

    length = request.headers.get('content-length')
    data = b""

    if length is None:
        data += request.content
    else:
        dl = 0
        length = int(length)
        for d in request.iter_content(chunk_size=65536):
            dl += len(d)
            data += d
            if callback: callback(dl, length)

    return data

def unarchive_file(file, dst):
    # assume that file is txz
    file = lzma.decompress(file)
    with tarfile.TarFile(fileobj=io.BytesIO(file)) as t:
        t.extractall(dst)

def cmd(binary, args):
    print(f'[c] "{binary}" {' '.join(args)}')
    subprocess.run([binary, *args])

def dl_callback(val, max_val):
    print(f'[p] {round(val/max_val*100):>3}%', end="\r")

def mkdir(path): os.makedirs(path, exist_ok=True)

def run(mod_url, game_folder):
    log("downloading the mod")
    mod = download_file(mod_url, dl_callback)
    print("[p] done")

    log("creating tempcontent folder")
    tempcontent_folder = os.path.join(game_folder, "portal2_tempcontent")

    if os.path.isdir(tempcontent_folder):
        log("found tempcontent folder! deleting it")
        shutil.rmtree(tempcontent_folder)
    os.mkdir(tempcontent_folder)

    log("installing the mod")
    unarchive_file(mod, tempcontent_folder)

    log("copying soundcache")
    src = os.path.join(game_folder, "portal2/maps/soundcache/_master.cache")
    dst = os.path.join(tempcontent_folder, "maps/soundcache/_master.cache")
    mkdir(os.path.dirname(dst))
    if os.path.isfile(src): shutil.copy(src, dst)
    else:
        src = os.path.join(game_folder, "portal2_dlc1/maps/soundcache/_master.cache")
        if os.path.isfile(src): shutil.copy(src, dst)
        else:
            src = os.path.join(game_folder, "portal2_dlc2/maps/soundcache/_master.cache")
            if os.path.isfile(src): shutil.copy(src, dst)
            else:
                log("no soundcache found")

    log("starting the game")
    cmd(os.path.join(game_folder, "portal2.exe"), ["-tempcontent", "-netconport", "22333"])

    log("game had closed, deleting the mod")
    shutil.rmtree(tempcontent_folder)

def details(package):
    print()
    log(f"title: {package["title"]}")
    log(f"description:")
    for i in package["description"].split("<br>"):
        log(i)
    log(f"author(s): {package["author"]}")
    log("[r]un it, [d]ownload and extract it or go [b]ack?")
    op = ask()
    while op not in "rbd" or len(op) != 1:
        op = ask()
    return op

def menu(repo):
    for k, i in enumerate(repo["packages"], start=1):
        log(f'{k:>3}. {i['title']}')
    log(f'  q. quit the application')

    cmd = ask()
    while cmd not in map(lambda x: str(x+1), range(len(repo["packages"]))) and cmd != "q":
        cmd = ask()
    
    if cmd == "q": exit()
    else:
        cmd = int(cmd)-1
        op = details(repo["packages"][cmd])
        if op == "b": menu(repo)
        elif op == "r": run(repo["packages"][cmd]["file"], config["portal_path"])
        elif op == "d":
            log("downloading mod")
            mod = download_file(repo["packages"][cmd]["file"], callback=dl_callback)
            print("[p] done")
            unarchive_file(mod, repo["packages"][cmd]["name"])
            log(f"unarchived at `{repo["packages"][cmd]["name"]}`")

def fetch_repo(repo_url):
    return requests.get(repo_url).json()

def is_portal_path(path):
    return os.path.isfile(os.path.join(path, "portal2.exe"))

def load_config():
    if not os.path.isfile("config.json"):
        json.dump({"portal_path": None, "repo_path": "https://www.p2r3.com/spplice/repo2/index.json"}, open("config.json", "w"))
    return json.load(open("config.json"))

def save_config(config):
    json.dump(config, open("config.json", "w"))

config = load_config()

if __name__ == "__main__":
    if not config["portal_path"]:
        log("no portal path specified, presumably first run")
        log("write path to your portal 2 game")
        path = ask()
        while not is_portal_path(path):
            log("not a real portal 2 installation")
            path = ask()
        config["portal_path"] = path
        save_config(config)
    
    log("fetching mod repository")
    repo = fetch_repo(config["repo_path"])

    menu(repo)
