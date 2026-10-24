#!/usr/bin/env python3
import os, re, json, time, signal, threading, subprocess, socket
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

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
      "script": str(script) if script else "Not selected", "folders": scan()}

PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Minecraft Server Panel</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8effa;font:15px system-ui}main{max-width:1050px;margin:auto;padding:18px}
.card{background:#121c2e;border:1px solid #26344b;border-radius:14px;padding:16px;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.stat{font-size:24px;font-weight:bold;margin:7px 0}.muted{color:#9aabc2;font-size:13px}h1{font-size:24px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button,input{border:1px solid #34445e;border-radius:8px;padding:10px;background:#0b1424;color:#fff;font:inherit}button{cursor:pointer}.go{background:#126b4c}.stop{background:#77283a}.blue{background:#173e70}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#060b13;padding:12px;border-radius:9px;height:300px;overflow:auto;font:12px monospace}
input{width:100%}.field{flex:1;min-width:170px}.folder{padding:10px;border:1px solid #26344b;border-radius:9px;margin-top:8px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
@media(max-width:650px){.grid{grid-template-columns:repeat(2,1fr)}main{padding:10px}.stat{font-size:20px}}
</style></head><body><main><h1>⛏ Minecraft Server Panel</h1><div class="muted">Termux • Wi-Fi LAN • Port 8080 • No password</div><div id="notice" class="muted"></div>
<div class="grid"><div class="card"><div class="muted">STATUS</div><div id="state" class="stat">Offline</div></div><div class="card"><div class="muted">UPTIME</div><div id="up" class="stat">00:00:00</div></div><div class="card"><div class="muted">PLAYERS ONLINE</div><div id="players" class="stat">Unknown</div></div><div class="card"><div class="muted">JAVA RAM (RSS)</div><div id="ram" class="stat">Unknown</div><div class="muted">RAM used by Java • Free RAM: <span id="freeram">Unknown</span></div></div></div>
<div class="card"><h3>Server Control</h3><div id="folderline" class="muted"></div><div class="row" style="margin-top:12px"><button class="go" onclick="act('start')">▶ Start</button><button class="blue" onclick="act('restart')">↻ Restart</button><button class="stop" onclick="act('stop')">■ Stop</button><button class="stop" onclick="act('force')">Force Stop</button></div><p class="muted">Start the server from this panel for console access. A server started elsewhere cannot have its stdin attached automatically.</p><div class="muted">Panel PID: <span id="pid">—</span> • Java PID: <span id="jpid">—</span></div></div>
<div class="card"><h3>Existing Server Folder</h3><div class="muted">Detected folders inside ~/server</div><div class="row" style="margin:10px 0"><button class="blue" onclick="scan()">↻ Scan again</button></div><div id="folders"></div></div>
<div class="card"><h3>Server details</h3><div class="muted">Folder</div><div id="folder"></div><div class="muted" style="margin-top:8px">Server JAR</div><div id="jar"></div><div class="muted" style="margin-top:8px">Start script</div><div id="script"></div><div class="muted" style="margin-top:8px">Max heap (read from start.sh)</div><div id="heap"></div><p class="muted">The panel runs start.sh; it does not replace its Java flags. CPU and TPS are not displayed.</p></div>
<div class="card"><h3>⚙ server.properties Settings</h3><p class="muted">Edit settings for the selected server. Save writes to server.properties; restart Minecraft for most changes to apply.</p><div class="row" style="margin:10px 0"><button class="blue" onclick="loadProperties()">↻ Load settings</button><button class="go" onclick="saveProperties()">Save settings</button></div><div id="propstatus" class="muted"></div><div id="properties"></div></div>
<div class="card"><h3>Live Output / Web Console</h3><pre id="logs">Waiting for output…</pre><div class="row"><div class="field"><input id="cmd" placeholder="Minecraft command, e.g. list" onkeydown="if(event.key==='Enter')send()"></div><button class="go" onclick="send()">Send</button><button onclick="getlogs()">Refresh</button></div><p class="muted">Player count is read from logs/latest.log when available; joined/left messages update the count automatically.</p></div>
<p class="muted">No password is required. Use only on a trusted Wi-Fi network; do not expose port 8080 to the public internet.</p></main>
<script>

async function api(path,data){let r=await fetch(path,{method:data?'POST':'GET',headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});let d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function note(t){document.getElementById('notice').textContent=t}
function fmt(n){return [Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(x=>String(x).padStart(2,'0')).join(':')}
async function refresh(){try{let d=await api('/api/status');state.textContent=d.state;up.textContent=fmt(d.uptime);players.textContent=d.players==null?'Unknown':(d.max_players==null?String(d.players):d.players+' / '+d.max_players);ram.textContent=d.ram==null?'Unknown':d.ram+' MB';freeram.textContent=d.free_ram==null?'Unknown':d.free_ram+' MB';pid.textContent=d.pid||'—';jpid.textContent=d.java_pid||'—';folderline.textContent=d.folder+' • '+d.jar;folder.textContent=d.folder;jar.textContent=d.jar;script.textContent=d.script;heap.textContent=d.heap;if(!document.getElementById('folders').dataset.loaded)renderFolders(d.folders)}catch(e){note(e.message)}}
function renderFolders(items){let root=document.getElementById('folders');root.innerHTML='';root.dataset.loaded='1';if(!items.length){root.textContent='No valid server folder found. A folder must contain server.jar and start.sh.';return}for(let x of items){let div=document.createElement('div');div.className='folder';let info=document.createElement('div');let b=document.createElement('button');b.className='blue';b.textContent='Use server';info.textContent=x.path+' [server.jar] [start.sh]';b.onclick=async()=>{try{let d=await api('/api/select',{path:x.path,jar:'server.jar'});note(d.message);root.dataset.loaded='';refresh();loadProperties()}catch(e){note(e.message)}};div.append(info,b);root.append(div)}}
async function act(a){if(a==='restart'&&!confirm('Restart Minecraft server?'))return;try{let d=await api('/api/'+a,{});note(d.message);setTimeout(refresh,500)}catch(e){note(e.message)}}
async function send(){let el=document.getElementById('cmd'),c=el.value.trim();if(!c)return;try{let d=await api('/api/command',{command:c});note(d.message);el.value='';getlogs()}catch(e){note(e.message)}}
async function scan(){try{let d=await api('/api/scan');renderFolders(d.folders);note('Scan complete')}catch(e){note(e.message)}}
async function getlogs(){try{let d=await api('/api/logs');logs.textContent=d.logs.join('\n')||'No output yet';logs.scrollTop=logs.scrollHeight}catch(e){note(e.message)}}
async function loadProperties(){try{let d=await api('/api/properties');let root=document.getElementById('properties');root.textContent='';for(let item of d.properties){let row=document.createElement('div');row.className='folder';row.style.alignItems='center';let label=document.createElement('label');label.style.flex='1';label.style.minWidth='180px';label.textContent=item.key;let input=document.createElement('input');input.style.flex='2';input.style.minWidth='180px';input.dataset.key=item.key;input.value=item.value;input.autocomplete='off';row.append(label,input);root.append(row)}document.getElementById('propstatus').textContent='Loaded '+d.properties.length+' properties from '+d.path}catch(e){document.getElementById('propstatus').textContent=e.message}}
async function saveProperties(){let values={};document.querySelectorAll('#properties input[data-key]').forEach(el=>values[el.dataset.key]=el.value);try{let d=await api('/api/properties',{values});document.getElementById('propstatus').textContent=d.message}catch(e){document.getElementById('propstatus').textContent=e.message}}
refresh();getlogs();loadProperties();setInterval(refresh,2000);setInterval(getlogs,1800);
</script></body></html>'''

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
        if path=="/api/properties":
            propfile = folder / "server.properties"
            if not propfile.is_file(): self.reply({"error":"server.properties not found in selected folder."},404); return
            try:
                props=[]
                for line in propfile.read_text(encoding="utf-8", errors="replace").splitlines():
                    stripped=line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in line: continue
                    key,value=line.split("=",1); props.append({"key":key.strip(),"value":value})
                self.reply({"path":str(propfile),"properties":props})
            except OSError as e: self.reply({"error":str(e)},500)
        elif path=="/api/status": self.reply(status())
        elif path=="/api/logs":
            with lock: self.reply({"logs":list(logs)})
        elif path=="/api/scan": self.reply({"folders":scan()})
        else: self.reply({"error":"Not found"},404)
    def do_POST(self):
        try: data=json.loads(self.rfile.read(min(int(self.headers.get("Content-Length","0")),20000)) or b"{}")
        except Exception: data={}
        path=urlparse(self.path).path
        if path=="/api/properties":
            propfile=folder / "server.properties"
            if not propfile.is_file(): self.reply({"error":"server.properties not found in selected folder."},404); return
            values=data.get("values")
            if not isinstance(values,dict): self.reply({"error":"Invalid settings payload."},400); return
            try:
                lines=propfile.read_text(encoding="utf-8",errors="replace").splitlines(keepends=True)
                updated=set(); out=[]
                for line in lines:
                    bare=line.rstrip("\r\n")
                    if bare.strip() and not bare.lstrip().startswith("#") and "=" in bare:
                        key=bare.split("=",1)[0].strip()
                        if key in values:
                            value=str(values[key])
                            if "\n" in value or "\r" in value: self.reply({"error":"Setting values cannot contain new lines."},400); return
                            ending="\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                            out.append(key+"="+value+ending); updated.add(key); continue
                    out.append(line)
                for key,value in values.items():
                    key=str(key)
                    if not re.fullmatch(r"[A-Za-z0-9_.-]+",key): self.reply({"error":"Invalid property key."},400); return
                    if key not in updated:
                        value=str(value)
                        if "\n" in value or "\r" in value: self.reply({"error":"Setting values cannot contain new lines."},400); return
                        out.append(key+"="+value+"\n")
                temp=propfile.with_name("server.properties.panel-tmp")
                temp.write_text("".join(out),encoding="utf-8"); os.replace(temp,propfile)
                addlog("Updated server.properties from panel.")
                self.reply({"ok":True,"message":"Saved server.properties successfully. Restart Minecraft to apply most changes."})
            except OSError as e: self.reply({"error":str(e)},500)
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
    print("No password required. Use on a trusted Wi-Fi network only.")
    print("Stop panel with Ctrl+C.\n")
    try: ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt: print("\nPanel stopped; Minecraft process is not automatically stopped.")
