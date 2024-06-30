
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
    log("decompressing")
    file = lzma.decompress(file)
    with tarfile.TarFile(fileobj=io.BytesIO(file)) as t:
        log("unextracting")
        t.extractall(dst)

def cmd(binary, args):
    print(f'[$] "{binary}" {' '.join(args)}')
    subprocess.run([binary, *args])

def dl_callback(val, max_val, files=1, cf=0):
    print(f'[p] {round(val/max_val*(100/files)+(100/files*cf)):>3}%', end="\r")

def mkdir(path): os.makedirs(path, exist_ok=True)

def run(mod_url, game_folder):
    log("downloading the mod")
    if isinstance(mod_url, list):
        mods = []
        for k, i in enumerate(mod_url):
            mods.append(download_file(i, lambda x, y: dl_callback(x, y, len(mod_url), k)))
        mod = b""
        for i in mods: mod += i
    else:
        mod = download_file(mod_url, dl_callback)
        print("[p] done")
    run_custom(mod, game_folder)

def run_custom(mod, game_folder):
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
    for k, i in enumerate(repo, start=1):
        log(f'{k:>3}. {i['title']}')
    log(f'  c. select custom mod')
    log(f'  q. quit the application')

    cmd = ask()
    while cmd not in map(lambda x: str(x+1), range(len(repo))) and cmd != "q" and cmd != "c":
        cmd = ask()
    
    if cmd == "q": exit()
    elif cmd == "c":
        log("select file location (.tar.xz .txz)")
        file = ask()
        while not os.path.isfile(file):
            log("not a file")
            file = ask()
        run_custom(open(file, "rb").read(), config["portal_path"])
    else:
        cmd = int(cmd)-1
        op = details(repo[cmd])
        if op == "b": menu(repo)
        elif op == "r": run(repo[cmd]["file"], config["portal_path"])
        elif op == "d":
            log("downloading mod")
            mod = download_file(repo[cmd]["file"], callback=dl_callback)
            print("[p] done")
            unarchive_file(mod, repo[cmd]["name"])
            log(f"unarchived at `{repo[cmd]["name"]}`")

def fetch_repo(repo_url):
    req = requests.get(repo_url)
    if not req.ok: return None
    return req.json()

def is_portal_path(path):
    return os.path.isfile(os.path.join(path, "portal2.exe"))

def load_config():
    if not os.path.isfile("config.json"):
        json.dump({"portal_path": None, "repositories": ["https://www.p2r3.com/spplice/repo2/index.json", "https://thisisignitedoreo.github.io/sppite/index.json"]}, open("config.json", "w"))
    return json.load(open("config.json"))

def save_config(config):
    json.dump(config, open("config.json", "w"))

def error(string):
    print('[!]', string)

config = load_config()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))

    if not config["portal_path"]:
        log("no portal path specified, presumably first run")
        log("write path to your portal 2 game")
        path = ask()
        while not is_portal_path(path):
            log("not a real portal 2 installation")
            path = ask()
        config["portal_path"] = path
        save_config(config)
    
    log("fetching mod repositories")
    repo = []
    for i in config["repositories"]:
        log(f"fetching {i}")
        r = fetch_repo(i)
        if r is None:
            log("error, skipping")
            continue
        repo += r["packages"]
    
    if len(repo) == 0:
        error("none repositories are feteched. internet problems, presumably?")

    menu(repo)
