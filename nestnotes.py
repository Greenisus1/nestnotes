#!/usr/bin/env python3
"""Nestnotes - notebooks, notes and checkable tasks in the terminal.

Fullscreen curses UI, pure stdlib. One JSON file holds everything:
notebooks contain notes; note lines like "[ ] buy seed" are tasks you
can check off from the view screen. Nothing leaves the Pi.

MIT license, copyright Greenisus1. Built with AI assistance from my design.
"""
import curses, json, os, time

VERSION = "1.0.0"
APP_DIR = os.environ.get("NESTNOTES_HOME", "/root/nestnotes")
STORE = os.path.join(APP_DIR, "notes.json")


def load_store():
    try:
        return json.load(open(STORE))
    except Exception:
        return {"notebooks": [{"name": "Inbox", "notes": []}]}


def save_store(st):
    os.makedirs(APP_DIR, exist_ok=True)
    json.dump(st, open(STORE, "w"), indent=1)


def new_note(title):
    return {"title": title, "body": "", "mtime": int(time.time())}


def is_task(line):
    s = line.lstrip()
    return s.startswith("[ ]") or s.startswith("[x]")


def toggle_task(line):
    i = len(line) - len(line.lstrip())
    s = line[i:]
    if s.startswith("[ ]"):
        return line[:i] + "[x]" + s[3:]
    if s.startswith("[x]"):
        return line[:i] + "[ ]" + s[3:]
    return line


def task_counts(note):
    done = todo = 0
    for line in note["body"].splitlines():
        s = line.lstrip()
        if s.startswith("[x]"):
            done += 1
        elif s.startswith("[ ]"):
            todo += 1
    return done, todo


def search_notes(st, query):
    q = query.lower()
    hits = []
    for nb in st["notebooks"]:
        for n in nb["notes"]:
            if q in n["title"].lower() or q in n["body"].lower():
                hits.append((nb["name"], n))
    return hits


class Editor:
    """Minimal multi-line text editor state, driven one key at a time."""

    def __init__(self, text):
        self.lines = text.split("\n") if text else [""]
        self.y = self.x = 0

    def key(self, ch):
        """ch: int from getch. Returns None."""
        line = self.lines[self.y]
        if ch == curses.KEY_UP:
            self.y = max(0, self.y - 1)
        elif ch == curses.KEY_DOWN:
            self.y = min(len(self.lines) - 1, self.y + 1)
        elif ch == curses.KEY_LEFT:
            if self.x > 0:
                self.x -= 1
            elif self.y > 0:
                self.y -= 1
                self.x = len(self.lines[self.y])
        elif ch == curses.KEY_RIGHT:
            if self.x < len(line):
                self.x += 1
            elif self.y < len(self.lines) - 1:
                self.y += 1
                self.x = 0
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if self.x > 0:
                self.lines[self.y] = line[:self.x - 1] + line[self.x:]
                self.x -= 1
            elif self.y > 0:
                prev = self.lines[self.y - 1]
                self.lines[self.y - 1] = prev + line
                del self.lines[self.y]
                self.y -= 1
                self.x = len(prev)
        elif ch in (10, 13):
            self.lines[self.y] = line[:self.x]
            self.lines.insert(self.y + 1, line[self.x:])
            self.y += 1
            self.x = 0
        elif 32 <= ch < 127:
            self.lines[self.y] = line[:self.x] + chr(ch) + line[self.x:]
            self.x += 1
        self.x = min(self.x, len(self.lines[self.y]))

    def text(self):
        return "\n".join(self.lines)


# ---------- UI ----------

def header(scr, w, sub):
    scr.addnstr(0, 0, f" NESTNOTES v{VERSION} - {sub}".ljust(w - 1), w - 1,
                curses.A_REVERSE)


def keys(scr, h, w, s):
    scr.addnstr(h - 1, 0, s[:w - 1], w - 1, curses.A_REVERSE)


def prompt(scr, label):
    curses.echo()
    curses.curs_set(1)
    h, w = scr.getmaxyx()
    scr.addnstr(h - 3, 2, label + " ", w - 4, curses.A_BOLD)
    scr.refresh()
    try:
        v = scr.getstr(h - 3, 2 + len(label) + 1, 200).decode().strip()
    except Exception:
        v = ""
    curses.noecho()
    curses.curs_set(0)
    return v


def wrap(text, width):
    out = []
    for raw in text.split("\n"):
        words, cur = raw.split(), ""
        if not words:
            out.append("")
        for wd in words:
            if len(cur) + len(wd) + 1 > width:
                out.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            out.append(cur)
    return out or [""]


def view_notebooks(scr, st):
    sel, msg = 0, ""
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        header(scr, w, "notebooks")
        nbs = st["notebooks"]
        for row, nb in enumerate(nbs[:h - 4]):
            n = len(nb["notes"])
            open_tasks = sum(task_counts(x)[1] for x in nb["notes"])
            line = f"{nb['name']} ({n} notes" + \
                   (f", {open_tasks} open tasks" if open_tasks else "") + ")"
            attr = curses.A_REVERSE if row == sel else 0
            scr.addnstr(2 + row, 2, line.ljust(w - 4), w - 4, attr)
        if msg:
            scr.addnstr(h - 2, 2, msg, w - 4, curses.A_BOLD)
        keys(scr, h, w, "[enter] open  [a]dd  [d]elete  [/] search  [q]uit")
        scr.refresh()
        ch = scr.getch()
        msg = ""
        if ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(len(nbs) - 1, sel + 1)
        elif ch in (10, 13) and nbs:
            view_notes(scr, st, nbs[sel])
        elif ch == ord("a"):
            name = prompt(scr, "Notebook name:")
            if name:
                nbs.append({"name": name, "notes": []})
                save_store(st)
        elif ch == ord("d") and nbs:
            gone = nbs.pop(sel)
            sel = max(0, sel - 1)
            save_store(st)
            msg = f"Deleted {gone['name']} and its {len(gone['notes'])} notes."
            if not nbs:
                nbs.append({"name": "Inbox", "notes": []})
        elif ch == ord("/"):
            q = prompt(scr, "Search:")
            if q:
                view_search(scr, st, q)
        elif ch in (ord("q"), 27):
            return


def view_search(scr, st, q):
    hits = search_notes(st, q)
    sel = 0
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        header(scr, w, f"search: {q} ({len(hits)})")
        for row, (nbname, n) in enumerate(hits[:h - 4]):
            line = f"{nbname} / {n['title']}"
            attr = curses.A_REVERSE if row == sel else 0
            scr.addnstr(2 + row, 2, line.ljust(w - 4), w - 4, attr)
        keys(scr, h, w, "[enter] open  [q] back")
        scr.refresh()
        ch = scr.getch()
        if ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(max(0, len(hits) - 1), sel + 1)
        elif ch in (10, 13) and hits:
            view_note(scr, st, hits[sel][1])
        elif ch in (ord("q"), 27):
            return


def view_notes(scr, st, nb):
    sel, msg = 0, ""
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        header(scr, w, nb["name"])
        notes = nb["notes"]
        if not notes:
            scr.addnstr(3, 4, "Empty - press a for a new note.", w - 8)
        for row, n in enumerate(notes[:h - 4]):
            done, todo = task_counts(n)
            badge = f" [{done}/{done + todo} done]" if done + todo else ""
            line = f"{n['title']}{badge}"
            attr = curses.A_REVERSE if row == sel else 0
            scr.addnstr(2 + row, 2, line.ljust(w - 4), w - 4, attr)
        if msg:
            scr.addnstr(h - 2, 2, msg, w - 4, curses.A_BOLD)
        keys(scr, h, w, "[enter] open  [a]dd note  [d]elete  [q] back")
        scr.refresh()
        ch = scr.getch()
        msg = ""
        if ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(max(0, len(notes) - 1), sel + 1)
        elif ch in (10, 13) and notes:
            view_note(scr, st, notes[sel])
        elif ch == ord("a"):
            t = prompt(scr, "Note title:")
            if t:
                notes.insert(0, new_note(t))
                save_store(st)
                view_note(scr, st, notes[0], edit_first=True)
        elif ch == ord("d") and notes:
            gone = notes.pop(sel)
            sel = max(0, sel - 1)
            save_store(st)
            msg = f"Deleted {gone['title']}."
        elif ch in (ord("q"), 27):
            return


def view_note(scr, st, note, edit_first=False):
    top, sel = 0, 0
    if edit_first:
        edit_note(scr, st, note)
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        header(scr, w, note["title"][:w - 20])
        raw = note["body"].split("\n")
        lines = []   # (raw_index, display_text)
        for ri, raw_line in enumerate(raw):
            for piece in wrap(raw_line, w - 6):
                lines.append((ri, piece))
        if not lines:
            lines = [(0, "")]
        body = h - 4
        top = max(0, min(top, sel - body + 1)) if sel >= top + body else min(top, sel)
        for row, (ri, line) in enumerate(lines[top:top + body]):
            i = top + row
            task = is_task(line)
            disp = ("[x]" if line.lstrip().startswith("[x]") else "[ ]") + \
                   line.lstrip()[3:] if task else line
            attr = curses.A_REVERSE if i == sel and task else 0
            if task and line.lstrip().startswith("[x]"):
                attr |= curses.A_DIM
            scr.addnstr(2 + row, 2, disp.ljust(w - 4)[:w - 4], w - 4, attr)
        done, todo = task_counts(note)
        if done + todo:
            scr.addnstr(h - 2, 2, f"tasks: {done}/{done + todo} done", w - 4)
        keys(scr, h, w, "[j/k] move  [space] check/uncheck  [e]dit  [q] back")
        scr.refresh()
        ch = scr.getch()
        if ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(len(lines) - 1, sel + 1)
        elif ch == ord(" "):
            ri = lines[sel][0] if sel < len(lines) else -1
            if 0 <= ri < len(raw) and is_task(raw[ri]):
                raw[ri] = toggle_task(raw[ri])
                note["body"] = "\n".join(raw)
                note["mtime"] = int(time.time())
                save_store(st)
        elif ch == ord("e"):
            edit_note(scr, st, note)
        elif ch in (ord("q"), 27):
            return


def edit_note(scr, st, note):
    ed = Editor(note["body"])
    curses.curs_set(1)
    while True:
        scr.erase()
        h, w = scr.getmaxyx()
        header(scr, w, f"editing: {note['title'][:w - 26]}")
        top = max(0, ed.y - (h - 5))
        for row, line in enumerate(ed.lines[top:top + h - 4]):
            scr.addnstr(2 + row, 2, line, w - 4)
        keys(scr, h, w, "type to edit - [esc] save and close")
        scr.move(2 + ed.y - top, min(2 + ed.x, w - 2))
        scr.refresh()
        ch = scr.getch()
        if ch == 27:
            note["body"] = ed.text().rstrip("\n")
            note["mtime"] = int(time.time())
            save_store(st)
            curses.curs_set(0)
            return
        ed.key(ch)


def main(scr):
    curses.curs_set(0)
    st = load_store()
    view_notebooks(scr, st)
    save_store(st)


if __name__ == "__main__":
    curses.wrapper(main)
