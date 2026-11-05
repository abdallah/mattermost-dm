"""Self-check for the logic that needs no server."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

_path = str(pathlib.Path(__file__).resolve().parent.parent / "mm-dm")
_loader = importlib.machinery.SourceFileLoader("mm_dm", _path)
_spec = importlib.util.spec_from_loader("mm_dm", _loader)
mm = importlib.util.module_from_spec(_spec)
_loader.exec_module(mm)

ALEX = {"username": "alex", "first_name": "Alex", "last_name": "Doe"}


def at_hour(hour):
    return mock.patch.object(mm.time, "localtime", return_value=mock.Mock(tm_hour=hour))


class Greeting(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("MM_DM_GREETINGS_AM", None)
        os.environ.pop("MM_DM_GREETINGS_PM", None)

    def test_no_greeting_when_not_due(self):
        self.assertEqual(mm.greeting(ALEX, "no greeting (last spoke)"), "")

    def test_defaults_follow_time_of_day(self):
        with at_hour(9):
            self.assertIn(mm.greeting(ALEX, "greet"), mm.GREETINGS_AM)
        with at_hour(15):
            self.assertIn(mm.greeting(ALEX, "greet"), mm.GREETINGS_PM)

    def test_env_lists_replace_defaults(self):
        os.environ["MM_DM_GREETINGS_AM"] = "yo | yo"
        with at_hour(9):
            self.assertEqual(mm.greeting(ALEX, "greet"), "yo")

    def test_blank_env_list_falls_back(self):
        os.environ["MM_DM_GREETINGS_PM"] = " | "
        with at_hour(15):
            self.assertIn(mm.greeting(ALEX, "greet"), mm.GREETINGS_PM)


class Render(unittest.TestCase):
    def test_empty_hi_drops_blank_line(self):
        self.assertEqual(mm.render("{hi}\n\nhello {first_name}", ALEX, "no greeting"), "hello Alex")

    def test_due_hi_is_kept(self):
        with mock.patch.object(mm, "greeting", return_value="hey"):
            self.assertEqual(mm.render("{hi}\n\nok", ALEX, "greet"), "hey\n\nok")


class FakeApi:
    posts = []

    def call(self, method, path, body=None):
        if path == "/users/me":
            return {"id": "me", "username": "me"}
        if path == "/users/email/alex@example.com":
            return {"id": "a1", **ALEX}
        if path == "/users/email/nobody@example.com":
            raise RuntimeError("HTTP 404")
        if path == "/channels/direct":
            return {"id": "dm"}
        if method == "GET":
            return {"posts": {}}
        FakeApi.posts.append(body["message"])
        return {"id": "p1"}


class PreviewThenSend(unittest.TestCase):
    def setUp(self):
        FakeApi.posts = []
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (mock.patch.object(mm, "Api", FakeApi),
                        mock.patch.object(mm, "PENDING", os.path.join(tmp.name, "pending.json")),
                        mock.patch.object(mm, "CONTACTS_FILE", os.path.join(tmp.name, "contacts.json")),
                        mock.patch.object(mm, "render", lambda template, u, status: template),
                        mock.patch("sys.stdin", io.StringIO(""))):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.message = os.path.join(tmp.name, "msg")

    def run_cli(self, *args):
        with mock.patch.object(sys, "argv", ["mm-dm", *args]), contextlib.redirect_stdout(io.StringIO()):
            return mm.main()

    def preview(self, text, to):
        with open(self.message, "w") as f:
            f.write(text)
        return self.run_cli("--dry-run", "--to", to, "--message-file", self.message)

    def test_sends_exactly_the_preview_once(self):
        self.preview("hello", "alex@example.com")
        self.assertEqual(FakeApi.posts, [])
        self.assertEqual(self.run_cli("--send-pending"), 0)
        self.assertEqual(FakeApi.posts, ["hello"])
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            self.run_cli("--send-pending")
        self.assertEqual(FakeApi.posts, ["hello"])

    def test_failed_preview_cancels_the_older_one(self):
        self.preview("old text", "alex@example.com")
        self.preview("new text", "nobody@example.com")
        with self.assertRaises(SystemExit):
            self.run_cli("--send-pending")
        self.assertEqual(FakeApi.posts, [])


if __name__ == "__main__":
    unittest.main()
