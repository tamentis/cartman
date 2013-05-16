import unittest

from cartman import app, exceptions


class DummyBrowser:

    def open(self, url):
        pass


class DummyResponse:

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
        self.content = text


class TestableApp(app.CartmanApp):

    def __init__(self):
        app.CartmanApp.__init__(self)
        self.browser = DummyBrowser()
        self.trac_version = (0, 12)

    def _editor(self, filename):
        pass

    def _input(self, prompt):
        return ""

    def set_responses(self, responses):
        self.responses = []
        for args in responses:
            self.responses.append(DummyResponse(*args))

    def _read_config(self):
        self.base_url = "localhost"
        self.username = "nosetests"
        self.password = "nosetests"
        self.auth_type = "basic"
        self.verify_ssl_cert = True
        self.required_fields = ["To", "Milestone", "Component", "Subject"]
        self.default_fields = ["To", "Cc", "Subject", "Component", "Milestone"]

    def login(self):
        pass

    def get(self, query_string, data=None):
        return self.responses.pop(0)

    post = get


class DummyArgs:

    def __init__(self, command, parameters=[]):
        self.command = command
        self.open_after = False
        self.parameters = parameters
        self.site = "trac"
        self.add_comment = False
        self.message = None
        self.template = None


class AppUnitTest(unittest.TestCase):

    def _get_properties(self):
        return """var properties={
            "milestone": {"options": [ "meh1", "meh2"]},
            "component": {"options": [ "com1", "com2"]},
            "version": {"options": [ "v1", "v2"]},
            "status": {"options": [ "opened", "reopened", "closed"]},
            "type": {"options": [ "opened", "reopened", "closed"]},
            "priority": {"options": [ "1", "2", "3"]}
        };"""

    def setUp(self):
        app.CONFIG_LOCATIONS = [ "./tests/cartmanrc.tests" ]
        self.app = TestableApp()

    def test_run_help(self):
        args = DummyArgs("help")
        self.app.run(args)

    def test_run_report(self):
        args = DummyArgs("report", ["1"])
        self.app.set_responses([
            (200, u"""id\tstuff\n1\twoot"""),
        ])

        self.app.run(args)

    def test_run_view(self):
        args = DummyArgs("view", ["1"])
        self.app.set_responses([
            (200, u"""id\tstuff\n1\twoot"""),
        ])

        self.app.run(args)

    def test_run_open_on_request(self):
        args = DummyArgs("open", ["1"])
        self.app.set_responses([
            (200, u"""id\tstuff\n1\twoot"""),
        ])

        self.app.run(args)

    def test_run_properties(self):
        args = DummyArgs("properties", [])
        self.app.set_responses([
            (200, self._get_properties()),
        ])

        self.app.run(args)

    def test_run_comment(self):
        args = DummyArgs("comment", ["1"])
        args.message = "brilliant!"
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />"""), # time stamp
            (200, u""), # post
        ])

        self.app.run(args)

    def test_run_comment_no_message(self):
        args = DummyArgs("comment", ["1"])
        args.message = ""
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />"""), # time stamp
            (200, u""), # post
        ])

        self.assertRaises(exceptions.FatalError, self.app.run, args)

    def test_run_status(self):
        args = DummyArgs("status", ["1", "reopen"])
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />
                      <input type="radio" stuff name="action" value="reopen" />
                      <input type="radio" stuff name="action" value="close" />
                      """),
            (200, u""), # post
        ])

        self.app.run(args)

    def test_run_status(self):
        args = DummyArgs("status", ["1"])
        self.app.set_responses([
            (200, u"""hemene, hemene <label>leave</label>
            as stuffy
            </input>
            <input name="ts" value="1" />
                     <input type="radio" stuff name="action" value="reopen" />
                     <input type="radio" stuff name="action" value="close" />
                     """),
            (200, u""), # post
        ])

        self.app.run(args)
        # TODO: test return...

    def test_run_new(self):
        self.skipTest("too much file-system interaction, code needs work.")
        args = DummyArgs("new")
        self.app.set_responses([
            (200, self._get_properties()),
            (200, u"""<input name="ts" value="1" />
                      <input type="radio" stuff name="action" value="reopen" />
                      <input type="radio" stuff name="action" value="close" />
                      """),
            (200, u""), # post
        ])

        self.app.run(args)
