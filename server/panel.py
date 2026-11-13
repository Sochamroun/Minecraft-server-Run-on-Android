#!/usr/bin/env python3
import os, re, json, time, signal, threading, subprocess, socket, base64, shutil, hashlib, urllib.request, urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode, quote

HOME_DIR = Path.home().resolve()
ROOT = (HOME_DIR / "server").resolve()
HOST, PORT = "0.0.0.0", int(os.environ.get("PANEL_PORT", "8080"))
lock = threading.RLock()
proc = None
started_at = None
folder, jar, script = ROOT, None, None
logs = []
players, max_players = None, None
online_names = set()
latest_log_position = 0
latest_log_path = None

def addlog(s):
    with lock:
        logs.append(time.strftime("[%H:%M:%S] ") + str(s))
        del logs[:-800]

def valid_server_folder(p):
    return p.is_dir() and (p / "server.jar").is_file() and (p / "start.sh").is_file()

def scan():
    """Find only actual server folders under Termux home; never list dependency JARs."""
    found = []
    excluded = {".git", ".cache", "node_modules", "libraries", ".gradle", ".npm", ".minecraft_panel"}
    for current, dirs, files in os.walk(HOME_DIR):
        cur = Path(current)
        dirs[:] = [d for d in dirs if d not in excluded and not d.startswith(".")]
        if "server.jar" in files and "start.sh" in files:
            found.append({"path": str(cur.resolve()), "jars": ["server.jar"], "scripts": ["start.sh"]})
            dirs[:] = []
    return sorted(found, key=lambda x: (x["path"] != str(ROOT), x["path"]))

def select(path, jarname=None):
    global folder, jar, script, latest_log_path, latest_log_position, players, max_players, online_names
    p = Path(path).resolve()
    try: p.relative_to(HOME_DIR)
    except ValueError: raise ValueError("Choose a server folder inside " + str(HOME_DIR))
    if not valid_server_folder(p):
        raise ValueError("Selected folder must contain both server.jar and start.sh")
    if jarname and jarname != "server.jar": raise ValueError("Only server.jar is accepted")
    folder, jar, script = p, "server.jar", p / "start.sh"
    latest_log_path = p / "logs" / "latest.log"
    latest_log_position = 0
    players, max_players, online_names = None, None, set()
    addlog(f"Selected {folder} | server.jar | start.sh")

def update_latest_log():
    global latest_log_position, players, max_players, online_names
    lp = folder / "logs" / "latest.log"
    if not lp.is_file(): return
    try:
        size = lp.stat().st_size
        if size < latest_log_position: latest_log_position = 0
        with lp.open("r", encoding="utf-8", errors="ignore") as f:
            if latest_log_position:
                f.seek(latest_log_position)
            chunk = f.read()
            latest_log_position = f.tell()
        for line in chunk.splitlines():
            m = re.search(r"There are (\d+) of a max of (\d+) players online", line, re.I)
            if m: players, max_players = int(m.group(1)), int(m.group(2))
            elif re.search(r"There are no players online", line, re.I): players = 0
            m = re.search(r":\s*([A-Za-z0-9_]{1,16}) joined the game", line)
            if m:
                online_names.add(m.group(1))
                players = len(online_names)
            m = re.search(r":\s*([A-Za-z0-9_]{1,16}) left the game", line)
            if m:
                online_names.discard(m.group(1))
                players = len(online_names)
            # Most vanilla servers log the list response in the console/latest.log.
            m = re.search(r"There are (\d+) of a max of (\d+) players online:?(.*)", line, re.I)
            if m:
                players, max_players = int(m.group(1)), int(m.group(2))
                names = [x.strip() for x in m.group(3).split(",") if x.strip()]
                if names: online_names = set(names)
    except OSError:
        pass

def available_ram_mb():
    try:
        info = Path("/proc/meminfo").read_text(errors="ignore")
        m = re.search(r"^MemAvailable:\s+(\d+)\s+kB", info, re.M)
        return round(int(m.group(1)) / 1024) if m else None
    except OSError: return None

def running():
    return proc is not None and proc.poll() is None

def read_output(p):
    global players, max_players, online_names
    for raw in iter(p.stdout.readline, ""):
        if not raw: break
        line = raw.rstrip()
        m = re.search(r"There are\s+(\d+)\s+of a max of\s+(\d+)\s+players online", line, re.I)
        if m: players, max_players = int(m.group(1)), int(m.group(2))
        if re.search(r"There are no players online", line, re.I): players = 0
        m = re.search(r"There are (\d+) of a max of (\d+) players online:?(.*)", line, re.I)
        if m:
            players, max_players = int(m.group(1)), int(m.group(2))
            names = [x.strip() for x in m.group(3).split(",") if x.strip()]
            if names: online_names = set(names)
        addlog(line)
    addlog("Server output closed.")

def descendants(pid):
    found, todo = set(), [pid]
    while todo:
        parent = todo.pop()
        if parent in found: continue
        found.add(parent)
        try:
            for p in Path("/proc").iterdir():
                if not p.name.isdigit(): continue
                try:
                    s = (p / "status").read_text(errors="ignore")
                    m = re.search(r"^PPid:\s*(\d+)", s, re.M)
                    if m and int(m.group(1)) == parent: todo.append(int(p.name))
                except OSError: pass
        except OSError: pass
    return found

def java_pid():
    if not running(): return None
    for pid in descendants(proc.pid):
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="ignore")
            if "java" in cmd.lower() and (".jar" in cmd.lower() or "server" in cmd.lower()): return pid
        except OSError: pass
    return proc.pid

def ram(pid):
    if not pid: return None
    try:
        s = Path(f"/proc/{pid}/status").read_text(errors="ignore")
        m = re.search(r"^VmRSS:\s+(\d+)\s+kB", s, re.M)
        return round(int(m.group(1))/1024, 1) if m else None
    except OSError: return None

def heap():
    try:
        m = re.findall(r"-Xmx\s*([0-9]+[kKmMgGtT])", script.read_text(errors="ignore"))
        return m[-1].upper() if m else "Set by start.sh"
    except Exception: return "Unknown"

def start():
    global proc, started_at, players, max_players
    if running(): return False, "Server is already online."
    if not script or not script.is_file(): return False, "Select a folder containing start.sh first."
    try:
        # Run the user's shell script, not a Java command assembled by the panel.
        proc = subprocess.Popen(["bash", str(script)], cwd=str(folder), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                bufsize=1, start_new_session=True, env=os.environ.copy())
        started_at, players, max_players = time.time(), 0, 0
        addlog(f"Started {script} (PID {proc.pid})")
        threading.Thread(target=read_output, args=(proc,), daemon=True).start()
        return True, f"Started with PID {proc.pid}."
    except Exception as e: return False, str(e)

def stop(force=False):
    if not running(): return False, "Server is already offline."
    p = proc
    try:
        if force:
            os.killpg(p.pid, signal.SIGKILL)
            addlog("Force stop: SIGKILL sent.")
        else:
            try: p.stdin.write("stop\n"); p.stdin.flush()
            except Exception: pass
            addlog("Sent Minecraft command: stop")
            def wait_stop():
                try: p.wait(timeout=25); addlog("Server stopped.")
                except subprocess.TimeoutExpired:
                    try: os.killpg(p.pid, signal.SIGTERM); p.wait(timeout=5)
                    except Exception:
                        try: os.killpg(p.pid, signal.SIGKILL)
                        except Exception: pass
            threading.Thread(target=wait_stop, daemon=True).start()
        return True, "Force stop requested." if force else "Stop command sent."
    except Exception as e: return False, str(e)

def status():
    on = running()
    jp = java_pid() if on else None
    update_latest_log()
    return {"running": on, "state": "Online" if on else "Offline",
      "pid": proc.pid if on else None, "java_pid": jp,
      "uptime": int(time.time()-started_at) if on and started_at else 0,
      "players": players, "max_players": max_players, "ram": ram(jp),
      "free_ram": available_ram_mb(), "heap": heap(), "folder": str(folder), "jar": jar or "Not detected",
      "script": str(script) if script else "Not selected", "plugin_directory": str(plugin_directory()), "folders": scan()}

MODRINTH_API = "https://api.modrinth.com/v2"
MODRINTH_UA = "TermuxMinecraftPanel/1.0 (local server plugin manager)"


def modrinth_get(path, params=None):
    url = MODRINTH_API + path
    if params:
        url += "?" + urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": MODRINTH_UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Modrinth response is too large.")
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ValueError("Modrinth API error: HTTP " + str(e.code))
    except (urllib.error.URLError, TimeoutError) as e:
        raise ValueError("Cannot connect to Modrinth: " + str(e))


def plugin_directory():
    """The plugins folder always follows the currently selected server."""
    target = (folder / "plugins").resolve()
    try:
        target.relative_to(folder.resolve())
    except ValueError:
        raise ValueError("Invalid plugins directory.")
    if target.is_symlink():
        raise ValueError("The plugins directory cannot be a symbolic link.")
    return target


def list_installed_plugins():
    target = plugin_directory()
    if not target.is_dir():
        return []
    return sorted([{"name": x.name, "size": x.stat().st_size} for x in target.iterdir()
                   if x.is_file() and not x.is_symlink() and x.suffix.lower() == ".jar"],
                  key=lambda x: x["name"].lower())


def get_plugin_versions(project, loader="paper", game_version=""):
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,64}", str(project)):
        raise ValueError("Invalid Modrinth project ID/slug.")
    if loader not in ("paper", "spigot", "bukkit", "purpur"):
        raise ValueError("Unsupported plugin loader.")
    api_loader = "paper" if loader == "purpur" else loader
    params = {"loaders": json.dumps([api_loader])}
    if game_version:
        if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", game_version):
            raise ValueError("Invalid Minecraft version.")
        params["game_versions"] = json.dumps([game_version])
    versions = modrinth_get("/project/" + quote(project, safe="") + "/version", params)
    result = []
    for v in versions:
        files = v.get("files") or []
        primary = next((f for f in files if f.get("primary")), files[0] if files else None)
        if not primary or not str(primary.get("filename", "")).lower().endswith(".jar"):
            continue
        result.append({"id": v.get("id"), "version": v.get("version_number"),
                       "game_versions": v.get("game_versions", []), "loaders": v.get("loaders", []),
                       "version_type": v.get("version_type", "release"), "filename": primary.get("filename")})
    return result


def install_modrinth_plugin(project, version_id, replace_existing=False):
    if running():
        raise ValueError("Stop the Minecraft server before installing plugins.")
    if not valid_server_folder(folder):
        raise ValueError("Select a valid server folder first.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,64}", str(project)) or not re.fullmatch(r"[A-Za-z0-9_-]{2,64}", str(version_id)):
        raise ValueError("Invalid project or version ID.")
    version = modrinth_get("/version/" + quote(version_id, safe=""))
    if version.get("project_id") != project:
        raise ValueError("This version does not belong to the selected project.")
    files = version.get("files") or []
    file_info = next((f for f in files if f.get("primary")), files[0] if files else None)
    if not file_info:
        raise ValueError("This version has no downloadable file.")
    filename = Path(str(file_info.get("filename", ""))).name
    if not filename.lower().endswith(".jar") or filename in ("", ".", ".."):
        raise ValueError("Modrinth did not provide a valid JAR filename.")
    url = str(file_info.get("url", ""))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("cdn.modrinth.com", "cdn-raw.modrinth.com"):
        raise ValueError("Refusing an untrusted download URL.")
    target_dir = plugin_directory()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError("The target path is not a regular plugin file.")
    if target.exists() and not replace_existing:
        raise ValueError("A file named " + filename + " already exists. Confirm replacement to update it.")
    req = urllib.request.Request(url, headers={"User-Agent": MODRINTH_UA})
    temp = target.with_name(target.name + ".download")
    digest = hashlib.sha512()
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=45) as response, temp.open("wb") as out:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise ValueError("Plugin file exceeds the 100 MB safety limit.")
                digest.update(chunk)
                out.write(chunk)
        expected = (file_info.get("hashes") or {}).get("sha512")
        if expected and digest.hexdigest().lower() != expected.lower():
            raise ValueError("SHA-512 verification failed; file was not installed.")
        if total == 0:
            raise ValueError("Downloaded file is empty.")
        os.replace(temp, target)
    except Exception:
        try: temp.unlink()
        except OSError: pass
        raise
    addlog("Installed Modrinth plugin: " + filename + " (" + str(version.get("version_number", "unknown")) + ")")
    return {"filename": filename, "size": total, "directory": str(target_dir), "version": version.get("version_number")}


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Minecraft Server Panel</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8effa;font:15px system-ui}main{max-width:1050px;margin:auto;padding:18px}
.card{background:#121c2e;border:1px solid #26344b;border-radius:14px;padding:16px;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.stat{font-size:24px;font-weight:bold;margin:7px 0}.muted{color:#9aabc2;font-size:13px}h1{font-size:24px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button,input,select,textarea{border:1px solid #34445e;border-radius:8px;padding:10px;background:#0b1424;color:#fff;font:inherit}button{cursor:pointer}.go{background:#126b4c}.stop{background:#77283a}.blue{background:#173e70}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#060b13;padding:12px;border-radius:9px;height:300px;overflow:auto;font:12px monospace}
input,select,textarea{width:100%}.field{flex:1;min-width:170px}.folder{padding:10px;border:1px solid #26344b;border-radius:9px;margin-top:8px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
.nav{display:flex;gap:8px;margin:16px 0}.nav button{flex:1}.nav button.active{background:#245b91;border-color:#4b8dcc}.view{display:none}.view.active{display:block}
textarea#filecontent{min-height:42vh;resize:vertical;font:13px/1.5 monospace;white-space:pre;tab-size:4}
.file-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:12px 0}.crumb{overflow-wrap:anywhere;color:#9aabc2;margin:10px 0}.entry{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px;border:1px solid #34445e;border-radius:9px;margin:7px 0;background:#0b1424}.entry-main{display:flex;align-items:center;gap:10px;min-width:0;flex:1}.entry-name{overflow-wrap:anywhere}.entry-actions{display:flex;gap:6px;flex-wrap:wrap}.entry button{padding:8px 10px}.danger{background:#77283a}.plugin-card{border:1px solid #34445e;border-radius:10px;padding:12px;margin:9px 0;background:#0b1424}.plugin-card img{width:42px;height:42px;object-fit:cover;border-radius:9px}.plugin-card-head{display:flex;gap:10px;align-items:center}.plugin-card select{max-width:100%}.pagination{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:14px 0}.pagination button{min-width:38px;padding:8px}.pagination button.active{background:#245b91;border-color:#75aee8}.pagination button:disabled{opacity:.4;cursor:not-allowed}.page-jump{width:78px}.upload-label{display:inline-flex;align-items:center;gap:7px;padding:10px 13px;background:#173e70;border:1px solid #34445e;border-radius:8px;cursor:pointer}
@media(max-width:650px){.grid{grid-template-columns:repeat(2,1fr)}main{padding:10px}.stat{font-size:20px}}
</style></head><body><main><h1>⛏ Minecraft Server Panel</h1><div class="muted">Termux • Wi-Fi LAN • Port 8080 • No password</div><div id="notice" class="muted"></div>
<div class="nav"><button id="navdash" class="active" onclick="showView('dashboard')">Dashboard</button><button id="naveditor" onclick="showView('editor')">Configuration editor</button><button id="navplugins" onclick="showView('plugins')">🧩 Plugins</button></div>
<section id="dashboard" class="view active">
<div class="grid"><div class="card"><div class="muted">STATUS</div><div id="state" class="stat">Offline</div></div><div class="card"><div class="muted">UPTIME</div><div id="up" class="stat">00:00:00</div></div><div class="card"><div class="muted">PLAYERS ONLINE</div><div id="players" class="stat">Unknown</div></div><div class="card"><div class="muted">JAVA RAM (RSS)</div><div id="ram" class="stat">Unknown</div><div class="muted">RAM used by Java • Free RAM: <span id="freeram">Unknown</span></div></div></div>
<div class="card"><h3>Server Control</h3><div id="folderline" class="muted"></div><div class="row" style="margin-top:12px"><button class="go" onclick="act('start')">▶ Start</button><button class="blue" onclick="act('restart')">↻ Restart</button><button class="stop" onclick="act('stop')">■ Stop</button><button class="stop" onclick="act('force')">Force Stop</button></div><p class="muted">Start the server from this panel for console access. A server started elsewhere cannot have its stdin attached automatically.</p><div class="muted">Panel PID: <span id="pid">—</span> • Java PID: <span id="jpid">—</span></div></div>
<div class="card"><h3>Existing Server Folder</h3><div class="muted">Detected folders inside Termux home</div><div class="row" style="margin:10px 0"><button class="blue" onclick="scan()">↻ Scan again</button></div><div id="folders"></div></div>
<div class="card"><h3>Server details</h3><div class="muted">Folder</div><div id="folder"></div><div class="muted" style="margin-top:8px">Server JAR</div><div id="jar"></div><div class="muted" style="margin-top:8px">Start script</div><div id="script"></div><div class="muted" style="margin-top:8px">Max heap (read from start.sh)</div><div id="heap"></div><p class="muted">The panel runs start.sh; it does not replace its Java flags. CPU and TPS are not displayed.</p></div>
<div class="card"><h3>Live Output / Web Console</h3><pre id="logs">Waiting for output…</pre><div class="row"><div class="field"><input id="cmd" placeholder="Minecraft command, e.g. list" onkeydown="if(event.key==='Enter')send()"></div><button class="go" onclick="send()">Send</button><button onclick="getlogs()">Refresh</button></div><p class="muted">Player count is read from logs/latest.log when available; joined/left messages update the count automatically.</p></div>
</section>
<section id="editor" class="view">
<div class="card"><h3>File manager</h3><p class="muted">Browse and manage files inside the server folder selected on the Dashboard. Folder navigation, editing, upload and delete are restricted to that folder.</p>
<div class="muted">Selected server folder</div><div id="editorfolder" style="overflow-wrap:anywhere;margin:5px 0 12px"></div>
<div class="file-toolbar"><button class="blue" onclick="goUp()">back</button><button class="blue" onclick="loadDirectory()">↻ Refresh</button><label class="upload-label"> Upload files<input id="uploadfiles" type="file" multiple hidden onchange="uploadFiles(this.files)"></label></div>
<div id="breadcrumb" class="crumb">/ (server root)</div><div id="fileentries"><div class="muted">Loading folder…</div></div>
<div id="filestatus" class="muted" style="margin:14px 0">Open a text file to edit it.</div>
<div id="editorbox" hidden><div class="row" style="justify-content:space-between;margin-bottom:8px"><strong id="openedpath"></strong><button class="go" onclick="saveFile()">Save changes</button></div><textarea id="filecontent" spellcheck="false" placeholder="File content"></textarea></div>
</div></section>
<section id="plugins" class="view">
<div class="card"><h3>🧩 Modrinth Plugin Manager</h3>
<p class="muted">Search and install Minecraft server plugins from Modrinth. The destination follows the server selected on Dashboard.</p>
<div class="muted">Current server</div><div id="pluginserver" style="overflow-wrap:anywhere;margin:5px 0"></div>
<div class="muted">Install directory</div><div id="plugindir" style="overflow-wrap:anywhere;margin:5px 0 12px"></div>
<div class="row"><div class="field"><label class="muted">Plugin name / keyword (optional)</label><input id="pluginquery" placeholder="Leave blank to browse all compatible plugins" onkeydown="if(event.key==='Enter')searchPlugins(1)"></div><button class="go" onclick="searchPlugins(1)">🔎 Search Modrinth</button></div>
<div class="row" style="margin-top:10px"><div class="field"><label class="muted">Server loader</label><select id="pluginloader"><option value="paper">Paper</option><option value="spigot">Spigot</option><option value="bukkit">Bukkit</option><option value="purpur">Purpur</option></select></div><div class="field"><label class="muted">Minecraft version (required)</label><input id="pluginmcversion" inputmode="decimal" placeholder="e.g. 1.21.4" onkeydown="if(event.key==='Enter')searchPlugins(1)"></div></div>
<p class="muted">Enter the Minecraft version, choose your server loader, and press Search. Leave the keyword blank to browse all compatible plugins, or enter a name to narrow the results.</p>
<div id="pluginstatus" class="muted" style="margin:12px 0">Search Modrinth to find plugins.</div><div id="pluginresults"></div><div id="pluginpagination" class="pagination" aria-label="Modrinth search pages"></div></div>
<div class="card"><div class="row" style="justify-content:space-between"><h3>Installed Plugins</h3><button class="blue" onclick="loadInstalledPlugins()">↻ Refresh</button></div><div id="installedplugins" class="muted">Loading…</div></div>
<div class="card"><p class="muted">Safety: plugins are third-party code and can change server behavior. Install only projects you trust. Stop the server before installing or removing a plugin; restart it after changes.</p></div>
</section>
<p class="muted">No password is required. Use only on a trusted Wi-Fi network; do not expose port 8080 to the public internet.</p></main>
<script>
let selectedFile='', currentDir='';
let pluginPage=1, pluginTotalPages=1, pluginQuery='';
async function api(path,data){let r=await fetch(path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});let d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function note(t){document.getElementById('notice').textContent=t}
function showView(which){document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id===which));document.getElementById('navdash').classList.toggle('active',which==='dashboard');document.getElementById('naveditor').classList.toggle('active',which==='editor');document.getElementById('navplugins').classList.toggle('active',which==='plugins');if(which==='editor')loadDirectory();if(which==='plugins'){loadInstalledPlugins();syncPluginFolder()}}
function fmt(n){return [Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(x=>String(x).padStart(2,'0')).join(':')}
async function refresh(){try{let d=await api('/api/status');state.textContent=d.state;up.textContent=fmt(d.uptime);players.textContent=d.players==null?'Unknown':(d.max_players==null?String(d.players):d.players+' / '+d.max_players);ram.textContent=d.ram==null?'Unknown':d.ram+' MB';freeram.textContent=d.free_ram==null?'Unknown':d.free_ram+' MB';pid.textContent=d.pid||'—';jpid.textContent=d.java_pid||'—';folderline.textContent=d.folder+' • '+d.jar;folder.textContent=d.folder;jar.textContent=d.jar;script.textContent=d.script;heap.textContent=d.heap;editorfolder.textContent=d.folder;document.getElementById('pluginserver').textContent=d.folder;document.getElementById('plugindir').textContent=d.folder+'/plugins';if(!document.getElementById('folders').dataset.loaded)renderFolders(d.folders)}catch(e){note(e.message)}}
function renderFolders(items){let root=document.getElementById('folders');root.innerHTML='';root.dataset.loaded='1';if(!items.length){root.textContent='No valid server folder found. A folder must contain server.jar and start.sh.';return}for(let x of items){let div=document.createElement('div');div.className='folder';let info=document.createElement('div');let b=document.createElement('button');b.className='blue';b.textContent='Use server';info.textContent=x.path+' [server.jar] [start.sh]';b.onclick=async()=>{try{let d=await api('/api/select',{path:x.path,jar:'server.jar'});note(d.message);root.dataset.loaded='';selectedFile='';currentDir='';document.getElementById('editorbox').hidden=true;refresh();loadDirectory()}catch(e){note(e.message)}};div.append(info,b);root.append(div)}}
async function act(a){if(a==='restart'&&!confirm('Restart Minecraft server?'))return;try{let d=await api('/api/'+a,{});note(d.message);setTimeout(refresh,500)}catch(e){note(e.message)}}
async function send(){let el=document.getElementById('cmd'),c=el.value.trim();if(!c)return;try{let d=await api('/api/command',{command:c});note(d.message);el.value='';getlogs()}catch(e){note(e.message)}}
async function scan(){try{let d=await api('/api/scan');renderFolders(d.folders);note('Scan complete')}catch(e){note(e.message)}}
async function getlogs(){try{let d=await api('/api/logs');logs.textContent=d.logs.join('\n')||'No output yet';logs.scrollTop=logs.scrollHeight}catch(e){note(e.message)}}
function node(tag,cls,txt){let n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n}
async function loadDirectory(){try{let d=await api('/api/browse?path='+encodeURIComponent(currentDir));currentDir=d.path;document.getElementById('editorfolder').textContent=d.folder;document.getElementById('breadcrumb').textContent=d.path?'/'+d.path.split('/').join('/'):'/ (server root)';let root=document.getElementById('fileentries');root.innerHTML='';if(!d.entries.length){root.append(node('div','muted','This folder is empty.'));return}for(const item of d.entries){let row=node('div','entry'),main=node('div','entry-main'),name=node('div','entry-name',(item.type==='dir'?'📁 ':'📄 ')+item.name),actions=node('div','entry-actions');main.append(name);if(item.type==='dir'){let open=node('button','blue','Open');open.onclick=()=>{currentDir=[currentDir,item.name].filter(Boolean).join('/');selectedFile='';document.getElementById('editorbox').hidden=true;loadDirectory()};actions.append(open)}else{let open=node('button','blue','Edit');open.onclick=()=>openFile(item.path);actions.append(open)}let del=node('button','danger','Delete');del.onclick=()=>deleteEntry(item);actions.append(del);row.append(main,actions);root.append(row)}}catch(e){document.getElementById('filestatus').textContent=e.message}}
function goUp(){if(!currentDir)return;currentDir=currentDir.split('/').slice(0,-1).join('/');selectedFile='';document.getElementById('editorbox').hidden=true;loadDirectory()}
async function openFile(path){try{let d=await api('/api/file?path='+encodeURIComponent(path));selectedFile=d.path;document.getElementById('filecontent').value=d.content;document.getElementById('openedpath').textContent=d.path;document.getElementById('editorbox').hidden=false;document.getElementById('filestatus').textContent='Opened '+d.path+' ('+d.size+' bytes)'}catch(e){document.getElementById('filestatus').textContent=e.message}}
async function saveFile(){if(!selectedFile)return;if(!confirm('Save changes to '+selectedFile+'?'))return;try{let d=await api('/api/file',{path:selectedFile,content:document.getElementById('filecontent').value});document.getElementById('filestatus').textContent=d.message}catch(e){document.getElementById('filestatus').textContent=e.message}}
async function deleteEntry(item){let msg=item.type==='dir'?'Delete folder '+item.path+' and everything inside it?':'Delete file '+item.path+'?';if(!confirm(msg))return;try{let d=await api('/api/delete',{path:item.path});document.getElementById('filestatus').textContent=d.message;if(selectedFile===item.path){selectedFile='';document.getElementById('editorbox').hidden=true}loadDirectory()}catch(e){document.getElementById('filestatus').textContent=e.message}}
async function uploadFiles(files){if(!files||!files.length)return;for(const file of files){try{let encoded=await new Promise((resolve,reject)=>{let r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]);r.onerror=reject;r.readAsDataURL(file)});let d=await api('/api/upload',{directory:currentDir,name:file.name,data:encoded});document.getElementById('filestatus').textContent=d.message}catch(e){document.getElementById('filestatus').textContent='Upload failed: '+e.message;break}}document.getElementById('uploadfiles').value='';loadDirectory()}
async function syncPluginFolder(){try{let d=await api('/api/status');document.getElementById('pluginserver').textContent=d.folder;document.getElementById('plugindir').textContent=d.plugin_directory; }catch(e){document.getElementById('pluginstatus').textContent=e.message}}
function renderPluginPagination(){
 const root=document.getElementById('pluginpagination');root.innerHTML='';
 if(!pluginQuery)return;
 const back=node('button','blue','‹ Back');
 back.disabled=pluginPage<=1;
 back.onclick=()=>searchPlugins(pluginPage-1);
 const label=node('span','muted','Page '+pluginPage+' / '+pluginTotalPages);
 const next=node('button','blue','Next ›');
 next.disabled=pluginPage>=pluginTotalPages;
 next.onclick=()=>searchPlugins(pluginPage+1);
 root.append(back,label,next);
}
async function searchPlugins(page=1){
 const q=document.getElementById('pluginquery').value.trim();
 const loader=document.getElementById('pluginloader').value;
 const gameVersion=document.getElementById('pluginmcversion').value.trim();
 const status=document.getElementById('pluginstatus');
 if(!/^[0-9]+\.[0-9]+(?:\.[0-9]+)?$/.test(gameVersion)){
  status.textContent='Enter a valid Minecraft version, for example 1.21.4.';return;
 }
 const searchKey=[q,loader,gameVersion].join('|');
 if(searchKey!==pluginQuery){pluginQuery=searchKey;page=1}
 pluginPage=Math.max(1,Math.min(1000,Number(page)||1));
 const box=document.getElementById('pluginresults');box.innerHTML='';
 document.getElementById('pluginpagination').innerHTML='';
 status.textContent='Searching compatible plugins on Modrinth • Page '+pluginPage+'…';
 try{
  const url='/api/plugins/search?q='+encodeURIComponent(q)+'&loader='+encodeURIComponent(loader)+'&game_version='+encodeURIComponent(gameVersion)+'&page='+pluginPage;
  const d=await api(url);
  pluginTotalPages=Math.max(1,Math.min(1000,Math.ceil((d.total_hits||0)/20)));
  if(pluginPage>pluginTotalPages&&d.total_hits>0)return searchPlugins(pluginTotalPages);
  status.textContent=(d.total_hits||0).toLocaleString()+' compatible plugin result(s) • Page '+pluginPage+' / '+pluginTotalPages+' • Minecraft '+gameVersion+' • '+loader;
  if(!d.hits.length){box.textContent='No compatible plugins found. Check the Minecraft version and loader.';renderPluginPagination();return}
  for(const x of d.hits){
   const card=node('div','plugin-card'),head=node('div','plugin-card-head'),img=document.createElement('img');
   img.src=x.icon_url||'';img.alt='';img.onerror=()=>img.remove();
   const info=node('div','');info.append(node('strong','',x.title),node('div','muted',(x.author?'by '+x.author+' • ':'')+Number(x.downloads||0).toLocaleString()+' downloads'));
   head.append(img,info);card.append(head,node('p','muted',x.description||''));
   const controls=node('div','row'),versions=node('select');versions.style.flex='1';
   versions.append(new Option('Loading compatible versions…',''));
   const install=node('button','go','Install selected version');install.disabled=true;
   controls.append(versions,install);card.append(controls);box.append(card);
   (async()=>{
    try{
     const v=await api('/api/plugins/versions?project='+encodeURIComponent(x.project_id)+'&loader='+encodeURIComponent(loader)+'&game_version='+encodeURIComponent(gameVersion));
     versions.innerHTML='';
     if(!v.versions.length){versions.append(new Option('No compatible JAR versions',''));return}
     for(const item of v.versions){
      const label=item.version+' • '+item.version_type+(item.game_versions&&item.game_versions.length?' • MC '+item.game_versions.slice(0,3).join(', '):'');
      versions.append(new Option(label,item.id));
     }
     install.disabled=false;
    }catch(e){versions.innerHTML='';versions.append(new Option('Could not load versions',''));status.textContent=e.message}
   })();
   install.onclick=async()=>{
    const vid=versions.value;if(!vid)return;
    if(!confirm('Install this plugin into the selected server plugins folder?'))return;
    install.disabled=true;install.textContent='Installing…';
    try{
     const result=await api('/api/plugins/install',{project:x.project_id,version_id:vid,replace:true});
     status.textContent='Installed '+result.filename+' • '+Math.ceil(result.size/1024)+' KB';
     loadInstalledPlugins();
    }catch(e){status.textContent=e.message}
    finally{install.disabled=false;install.textContent='Install selected version'}
   };
  }
  renderPluginPagination();
 }catch(e){status.textContent=e.message}
}
async function loadInstalledPlugins(){let root=document.getElementById('installedplugins');if(!root)return;try{let d=await api('/api/plugins/installed');root.innerHTML='';if(!d.plugins.length){root.textContent='No plugins installed in '+d.directory;return}for(const p of d.plugins){let row=node('div','entry'),main=node('div','entry-main'),name=node('div','entry-name','🧩 '+p.name+' • '+Math.ceil(p.size/1024)+' KB'),actions=node('div','entry-actions'),find=node('button','blue','Find update'),del=node('button','danger','Remove');main.append(name);find.onclick=()=>{document.getElementById('pluginquery').value=p.name.replace(/\.jar$/i,'');searchPlugins();document.getElementById('pluginquery').scrollIntoView({behavior:'smooth',block:'center'})};actions.append(find,del);del.onclick=async()=>{if(!confirm('Remove '+p.name+' from this server?'))return;try{let r=await api('/api/plugins/remove',{name:p.name});document.getElementById('pluginstatus').textContent=r.message;loadInstalledPlugins()}catch(e){document.getElementById('pluginstatus').textContent=e.message}};row.append(main,actions);root.append(row)}}catch(e){root.textContent=e.message}}
refresh();getlogs();setInterval(refresh,2000);setInterval(getlogs,1800);
</script></body></html>'''


def safe_selected_path(relative="", must_exist=True):
    """Resolve a relative path without allowing traversal or symlink escapes."""
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("Choose a path inside the selected server folder.")
    parts = Path(relative).parts
    if any(part in ("..", "") for part in parts): raise ValueError("Invalid relative path.")
    base = folder.resolve(); candidate = base.joinpath(*parts)
    if must_exist: candidate = candidate.resolve(strict=True)
    else: candidate = candidate.parent.resolve(strict=True) / candidate.name
    try: candidate.relative_to(base)
    except ValueError: raise ValueError("Paths outside the selected server folder are not allowed.")
    if candidate != base and candidate.is_symlink(): raise ValueError("Symbolic links are not allowed.")
    return candidate

def safe_selected_file(relative):
    candidate=safe_selected_path(relative,True)
    if not candidate.is_file() or candidate.is_symlink(): raise ValueError("Selected path is not a regular file.")
    return candidate

def list_server_entries(relative=""):
    directory=safe_selected_path(relative,True)
    if not directory.is_dir() or directory.is_symlink(): raise ValueError("Selected path is not a folder.")
    entries=[]
    for item in directory.iterdir():
        if item.is_symlink(): continue
        try:
            item.resolve(strict=True).relative_to(folder.resolve())
            if item.is_dir(): entries.append({"name":item.name,"path":item.relative_to(folder).as_posix(),"type":"dir"})
            elif item.is_file(): entries.append({"name":item.name,"path":item.relative_to(folder).as_posix(),"type":"file","size":item.stat().st_size})
        except (OSError,ValueError): continue
    return sorted(entries,key=lambda x:(x["type"]!="dir",x["name"].lower()))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def reply(self, data, code=200):
        b=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(b)
    def auth(self):
        return True
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/":
            b=PAGE.encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
        if path=="/api/browse":
            try:
                relative=parse_qs(urlparse(self.path).query).get("path",[""])[0]
                self.reply({"folder":str(folder),"path":relative,"entries":list_server_entries(relative)})
            except (OSError,ValueError) as e: self.reply({"error":str(e)},400)
        elif path=="/api/files":
            if not valid_server_folder(folder): self.reply({"error":"Select a valid server folder first."},409); return
            self.reply({"folder":str(folder),"files":list_server_files()})
        elif path=="/api/file":
            try:
                relative=parse_qs(urlparse(self.path).query).get("path",[""])[0]
                target=safe_selected_file(relative)
                if target.stat().st_size > 2 * 1024 * 1024: self.reply({"error":"File is larger than the 2 MB editor limit."},413); return
                content=target.read_bytes()
                if b"\\0" in content: self.reply({"error":"Binary files cannot be edited in the text editor."},415); return
                self.reply({"path":target.relative_to(folder).as_posix(),"content":content.decode("utf-8"),"size":len(content)})
            except UnicodeDecodeError: self.reply({"error":"This file is not valid UTF-8 text."},415)
            except (OSError, ValueError) as e: self.reply({"error":str(e)},400)
        elif path=="/api/plugins/search":
            try:
                if not valid_server_folder(folder): raise ValueError("Select a valid server folder first.")
                query=parse_qs(urlparse(self.path).query).get("q",[""])[0].strip()[:100]
                loader=parse_qs(urlparse(self.path).query).get("loader",["paper"])[0]
                game_version=parse_qs(urlparse(self.path).query).get("game_version",[""])[0].strip()
                try: page=int(parse_qs(urlparse(self.path).query).get("page",["1"])[0])
                except (TypeError,ValueError): raise ValueError("Page must be a number from 1 to 1000.")
                if loader not in ("paper","spigot","bukkit","purpur"): raise ValueError("Unsupported loader.")
                if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", game_version):
                    raise ValueError("Enter a valid Minecraft version, for example 1.21.4.")
                if page < 1 or page > 1000: raise ValueError("Page must be between 1 and 1000.")
                # Filter Modrinth projects by plugin type, server loader and Minecraft version.
                facets=json.dumps([["all_project_types:plugin"],["categories:"+loader],["versions:"+game_version]])
                limit=20; offset=(page-1)*limit
                params={"facets":facets,"limit":str(limit),"offset":str(offset),"index":"downloads"}
                if query: params["query"]=query
                result=modrinth_get("/search",params)
                hits=[]
                for x in result.get("hits",[]):
                    types=x.get("all_project_types") or []
                    if "plugin" in types or x.get("project_type")=="plugin":
                        hits.append({"project_id":x.get("project_id"),"slug":x.get("slug"),"title":x.get("title"),"description":x.get("description"),"author":x.get("author"),"downloads":x.get("downloads"),"icon_url":x.get("icon_url")})
                self.reply({"hits":hits,"total_hits":int(result.get("total_hits",0)),"offset":offset,"page":page,"limit":limit})
            except Exception as e: self.reply({"error":str(e)},400)
        elif path=="/api/plugins/versions":
            try:
                q=parse_qs(urlparse(self.path).query)
                versions=get_plugin_versions(q.get("project",[""])[0],q.get("loader",["paper"])[0],q.get("game_version",[""])[0].strip())
                self.reply({"versions":versions})
            except Exception as e: self.reply({"error":str(e)},400)
        elif path=="/api/plugins/installed":
            try: self.reply({"directory":str(plugin_directory()),"plugins":list_installed_plugins()})
            except Exception as e: self.reply({"error":str(e)},400)
        elif path=="/api/status": self.reply(status())
        elif path=="/api/logs":
            with lock: self.reply({"logs":list(logs)})
        elif path=="/api/scan": self.reply({"folders":scan()})
        else: self.reply({"error":"Not found"},404)
    def do_POST(self):
        try: data=json.loads(self.rfile.read(min(int(self.headers.get("Content-Length","0")),14 * 1024 * 1024)) or b"{}")
        except Exception: data={}
        path=urlparse(self.path).path
        if path=="/api/delete":
            try:
                target=safe_selected_path(data.get("path"),True)
                if target==folder.resolve(): raise ValueError("The selected server root cannot be deleted.")
                rel=target.relative_to(folder.resolve()).as_posix()
                if target.is_dir(): shutil.rmtree(target)
                elif target.is_file(): target.unlink()
                else: raise ValueError("Unsupported filesystem entry.")
                addlog("Deleted from Configuration editor: "+rel)
                self.reply({"ok":True,"message":"Deleted "+rel})
            except (OSError,ValueError) as e: self.reply({"error":str(e)},400)
        elif path=="/api/upload":
            try:
                name=data.get("name"); encoded=data.get("data"); relative=data.get("directory","")
                if not isinstance(name,str) or not name or name in (".","..") or Path(name).name!=name or "/" in name or "\\" in name or name.startswith("."):
                    raise ValueError("Invalid upload filename.")
                if not isinstance(encoded,str): raise ValueError("No upload data received.")
                target_dir=safe_selected_path(relative,True)
                if not target_dir.is_dir(): raise ValueError("Upload destination is not a folder.")
                target=target_dir/name
                if target.exists() or target.is_symlink(): raise ValueError("A file or folder with that name already exists; rename it before uploading.")
                raw=base64.b64decode(encoded,validate=True)
                if len(raw)>10*1024*1024: raise ValueError("Upload limit is 10 MB per file.")
                target.write_bytes(raw)
                addlog("Uploaded into Configuration editor: "+target.relative_to(folder).as_posix())
                self.reply({"ok":True,"message":"Uploaded "+target.relative_to(folder).as_posix()})
            except (OSError,ValueError) as e: self.reply({"error":str(e)},400)
        elif path=="/api/file":
            try:
                relative=data.get("path")
                content=data.get("content")
                if not isinstance(content,str): self.reply({"error":"File content must be text."},400); return
                if len(content.encode("utf-8")) > 2 * 1024 * 1024: self.reply({"error":"File exceeds the 2 MB editor limit."},413); return
                target=safe_selected_file(relative)
                mode=target.stat().st_mode
                temp=target.with_name(target.name+".panel-tmp")
                temp.write_text(content,encoding="utf-8",newline="")
                os.chmod(temp,mode)
                os.replace(temp,target)
                addlog("Edited file from Configuration editor: "+target.relative_to(folder).as_posix())
                self.reply({"ok":True,"message":"Saved "+target.relative_to(folder).as_posix()})
            except (OSError, ValueError) as e:
                self.reply({"error":str(e)},400)
        elif path=="/api/plugins/install":
            try:
                result=install_modrinth_plugin(data.get("project",""),data.get("version_id",""),bool(data.get("replace",False)))
                self.reply({"ok":True,**result})
            except Exception as e: self.reply({"error":str(e)},400)
        elif path=="/api/plugins/remove":
            try:
                if running(): raise ValueError("Stop the Minecraft server before removing plugins.")
                name=data.get("name","")
                if not isinstance(name,str) or Path(name).name!=name or not name.lower().endswith(".jar"):
                    raise ValueError("Invalid plugin filename.")
                target=plugin_directory()/name
                if target.is_symlink() or not target.is_file(): raise ValueError("Plugin file not found.")
                target.unlink(); addlog("Removed plugin: "+name)
                self.reply({"ok":True,"message":"Removed "+name})
            except Exception as e: self.reply({"error":str(e)},400)
        elif path=="/api/start":
            ok,msg=start(); self.reply({"ok":ok,"message":msg},200 if ok else 409)
        elif path=="/api/stop":
            ok,msg=stop(); self.reply({"ok":ok,"message":msg},200 if ok else 409)
        elif path=="/api/force":
            ok,msg=stop(True); self.reply({"ok":ok,"message":msg},200 if ok else 409)
        elif path=="/api/restart":
            if running():
                stop(False)
                def later():
                    end=time.time()+35
                    while running() and time.time()<end: time.sleep(.5)
                    if not running(): start()
                    else: addlog("Restart cancelled: server did not stop in time.")
                threading.Thread(target=later,daemon=True).start(); self.reply({"ok":True,"message":"Restart queued."})
            else:
                ok,msg=start(); self.reply({"ok":ok,"message":msg},200 if ok else 409)
        elif path=="/api/command":
            cmd=str(data.get("command","")).strip()
            if not cmd or "\n" in cmd or "\r" in cmd: self.reply({"error":"Enter one command."},400)
            elif not running(): self.reply({"error":"Server is offline."},409)
            else:
                try: proc.stdin.write(cmd+"\n"); proc.stdin.flush(); addlog("> "+cmd); self.reply({"ok":True,"message":"Command sent."})
                except Exception as e: self.reply({"error":str(e)},500)
        elif path=="/api/select":
            if running(): self.reply({"error":"Stop server before changing folder."},409)
            else:
                try: select(str(data.get("path","")),str(data.get("jar","")) or None); self.reply({"ok":True,"message":"Selected "+str(folder)})
                except Exception as e: self.reply({"error":str(e)},400)
        else: self.reply({"error":"Not found"},404)

def wifi_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "<phone-wifi-ip>"

if __name__=="__main__":
    try: select(str(ROOT))
    except Exception as e: addlog("Choose a valid server folder from the panel: " + str(e))
    ip = wifi_ip()
    print("\n=== Termux Minecraft Web Panel ===")
    print("Local URL: http://127.0.0.1:%s" % PORT)
    print("Wi-Fi URL: http://%s:%s" % (ip, PORT))
    print("Server folders must contain both server.jar and start.sh.")
    print("Stop panel with Ctrl+C.\n")
    try: ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt: print("\nPanel stopped; Minecraft process is not automatically stopped.")
