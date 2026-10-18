import curses, importlib.util, os, tempfile, unittest

os.environ["NESTNOTES_HOME"] = tempfile.mkdtemp()
spec = importlib.util.spec_from_file_location(
    "nestnotes", os.path.join(os.path.dirname(__file__), "nestnotes.py"))
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


class TestTasks(unittest.TestCase):
    def test_toggle(self):
        self.assertEqual(n.toggle_task("[ ] buy seed"), "[x] buy seed")
        self.assertEqual(n.toggle_task("[x] buy seed"), "[ ] buy seed")
        self.assertEqual(n.toggle_task("  [ ] indented"), "  [x] indented")
        self.assertEqual(n.toggle_task("plain line"), "plain line")

    def test_counts(self):
        note = {"body": "[x] a\n[ ] b\ntext\n[ ] c"}
        self.assertEqual(n.task_counts(note), (1, 2))


class TestStore(unittest.TestCase):
    def test_roundtrip(self):
        st = {"notebooks": [{"name": "N", "notes": [n.new_note("t")]}]}
        n.save_store(st)
        self.assertEqual(n.load_store(), st)

    def test_search(self):
        st = {"notebooks": [
            {"name": "A", "notes": [{"title": "seeds", "body": "sunflower"}]},
            {"name": "B", "notes": [{"title": "other", "body": "sunflower too"}]},
        ]}
        self.assertEqual(len(n.search_notes(st, "sunflower")), 2)
        self.assertEqual(len(n.search_notes(st, "seeds")), 1)
        self.assertEqual(len(n.search_notes(st, "zzz")), 0)


class TestEditor(unittest.TestCase):
    def drive(self, ed, s):
        for ch in s:
            ed.key(ord(ch))

    def test_typing(self):
        ed = n.Editor("")
        self.drive(ed, "hello")
        self.assertEqual(ed.text(), "hello")

    def test_newline_and_backspace(self):
        ed = n.Editor("")
        self.drive(ed, "ab")
        ed.key(10)
        self.drive(ed, "cd")
        self.assertEqual(ed.text(), "ab\ncd")
        ed.key(127)
        self.assertEqual(ed.text(), "ab\nc")
        ed.key(127)
        self.assertEqual(ed.text(), "ab\n")
        ed.key(127)  # joins lines
        self.assertEqual(ed.text(), "ab")

    def test_arrows(self):
        ed = n.Editor("ab\ncd")
        ed.key(curses.KEY_DOWN)
        self.drive(ed, "X")
        self.assertEqual(ed.text(), "ab\nXcd")
        ed.key(curses.KEY_LEFT)   # x=0 on "cd"
        ed.key(curses.KEY_LEFT)   # wraps to end of "ab"
        self.drive(ed, "Y")
        self.assertEqual(ed.text(), "abY\nXcd")


if __name__ == "__main__":
    unittest.main()
