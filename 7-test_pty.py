"""PTY walkthrough: new note, type tasks in the editor, check one off, quit."""
import json, os, pty, re, select, sys, tempfile, time

home = tempfile.mkdtemp()
env = dict(os.environ, NESTNOTES_HOME=home, TERM="xterm-256color",
           LINES="30", COLUMNS="100")
pid, fd = pty.fork()
if pid == 0:
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
    os.execvpe(sys.executable, [sys.executable, "nestnotes.py"], env)

out = b""
def pump(t):
    global out
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try: out += os.read(fd, 65536)
            except OSError: break

fail = []
pump(2.0)
if not re.search(rb"NESTNOTES v1\.0\.0", out): fail.append("title")
os.write(fd, b"\r"); pump(0.8)         # open Inbox
os.write(fd, b"a"); pump(0.6)
os.write(fd, b"shopping\n"); pump(1.0) # editor opens on the new note
os.write(fd, b"[ ] seeds\r"); pump(0.5)
os.write(fd, b"[ ] suet"); pump(0.5)
os.write(fd, b"\x1b"); pump(0.8)       # esc: save + back to note view
os.write(fd, b" "); pump(0.8)          # check first task
os.write(fd, b"q"); pump(0.6)          # notes list
if not re.search(rb"\[1/2 done\]", out): fail.append("badge")
os.write(fd, b"q"); pump(0.6)          # notebooks
os.write(fd, b"q"); pump(0.8)          # quit
wp, _ = os.waitpid(pid, os.WNOHANG)
if wp == 0:
    try: os.kill(pid, 9); os.waitpid(pid, 0)
    except ProcessLookupError: pass
    fail.append("did not quit")
st = json.load(open(os.path.join(home, "notes.json")))
note = st["notebooks"][0]["notes"][0]
if note["title"] != "shopping": fail.append("store title")
if "[x] seeds" not in note["body"]: fail.append("store toggle")
if fail:
    print("PTY FAIL:", ", ".join(fail)); sys.exit(1)
print("PTY PASS")
