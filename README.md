# Nestnotes

Notebooks, notes and checkable tasks in a fullscreen terminal UI. Pure
Python standard library - no dependencies, no accounts, nothing leaves
the Pi. One JSON file holds everything.

## What it does

- **Notebooks** group your notes; add and delete with `a` / `d`.
- **Notes** have a title and freeform body, edited in a built-in
  fullscreen editor (`e`, plain typing, arrows, backspace, `esc` saves).
- **Tasks**: any note line like `[ ] buy seed` is a task. Check it off
  with `space` right from the note view; notebooks and note lists show
  done/total badges.
- **Search** (`/`) across every notebook, title and body.

## Install (Pi App Store)

Install through the Pi App Store, or:

```sh
sudo bash app-store.sh install   # checks Python/curses, compiles sources
sudo python3 nestnotes.py        # or: bash app-store.sh run
```

Data is stored in `/root/nestnotes/notes.json` (override with the
`NESTNOTES_HOME` environment variable).

## Tests

```sh
python3 test_nestnotes.py   # unit tests (tasks, store, search, editor)
python3 test_pty.py         # fullscreen walkthrough in a pty
```

MIT license, copyright Greenisus1. Built with AI assistance from my design.
