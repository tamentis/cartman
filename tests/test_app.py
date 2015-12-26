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
        self.output = None

    def editor(self, filename):
        pass

    def input(self, prompt):
        return ""

    def set_responses(self, responses):
        self.responses = []
        for args in responses:
            self.responses.append(DummyResponse(*args))

    def read_config(self):
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

    def print_output(self, output):
        """Store the output for testing purpose."""
        self.output = output

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
        self.message_file = None


class AppUnitTest(unittest.TestCase):

    def _get_properties(self):
        return """var properties={
            "milestone": {"options": [ "meh1", "meh2"]},
            "component": {"options": [ "com1", "com2"]},
            "version": {"options": [ "v1", "v2"]},
            "status": {"options": [ "opened", "reopened", "closed"]},
            "type": {"options": [ "opened", "reopened", "closed"]},
            "priority": {"options": [ "1", "2", "3"]}
        }; var modes={}; </script>Any; random; text."""

    def setUp(self):
        app.CONFIG_LOCATIONS = [ "./tests/cartmanrc.tests" ]
        self.app = TestableApp()

    def test_run_help(self):
        args = DummyArgs("help")
        self.app.run(args)

    def test_run_function_help(self):
        args = DummyArgs("report", [])
        self.app.set_responses([])
        self.app.run(args)

    def test_run_report(self):
        args = DummyArgs("report", ["1"])
        self.app.set_responses([
            (200, u"""id\tsummary\treporter\tdescription\n"""
                  u"""1\twoot\tsome_reporter\tany text\n"""
                  u"""2\tnope\tother_dude\tsomething\n"""),
        ])

        self.app.run(args)
        self.assertEquals(self.app.output, [
            '#1. woot (some_reporter)',
            '#2. nope (other_dude)',
        ])

    def test_run_view(self):
        args = DummyArgs("view", ["1"])
        self.app.set_responses([
            (200, u"""id\tsummary\treporter\tdescription\n"""
                  u"""1\twoot\tsome_reporter\tany text"""),
        ])

        self.app.run(args)
        self.assertEquals(self.app.output, [
            '#1. woot (some_reporter)\n------------------------',
            '',
            'any text'
        ])

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
        self.assertEquals(self.app.output, [
            'Milestones\n----------',
            u'meh1, meh2',
            '',
            'Components\n----------',
            u'com1, com2',
            '',
            'Status\n------',
            u'opened, reopened, closed',
            '',
            'Priorities\n----------',
            u'1, 2, 3',
            '',
        ])

    def test_run_comment(self):
        args = DummyArgs("comment", ["1"])
        args.message = "brilliant!"
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />"""), # time stamp
            (200, u""), # post
        ])

        self.app.run(args)
        self.assertIsNone(self.app.output)

    def test_run_comment_no_message(self):
        args = DummyArgs("comment", ["1"])
        args.message = ""
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />"""), # time stamp
            (200, u""), # post
        ])

        self.assertRaises(exceptions.FatalError, self.app.run, args)

    def test_run_status_set(self):
        args = DummyArgs("status", ["1", "reopen"])
        self.app.set_responses([
            (200, u"""<input name="ts" value="1" />
                      <input type="radio" stuff name="action" value="reopen" />
                      <input type="radio" stuff name="action" value="close" />
                      """),
            (200, u""), # post
        ])

        self.app.run(args)
        self.assertIsNone(self.app.output)

    def test_run_status_get_v1(self):
        args = DummyArgs("status", ["1"])
        self.app.trac_version = (1,0)
        self.app.set_responses([
            (200, u"""
                   <h2>
                     <a href="/testtrac-1.0.1/ticket/1" class="trac-id">#1</a>
                     <span class="trac-status">
                       <a href="/testtrac-1.0.1/query?status=accepted">accepted</a>
                     </span>
                     <span class="trac-type">
                       <a href="/testtrac-1.0.1/query?status=!closed&amp;type=defect">defect</a>
                     </span>
                   </h2>
                   """),
            (200, u""), # post
        ])

        self.app.run(args)
        self.assertEquals(self.app.output, ['Current status: accepted'])

    def test_run_status_get_v0(self):
        args = DummyArgs("status", ["1"])
        self.app.set_responses([
            (200, u"""
                   <h1 id="trac-ticket-title">
                       <a href="/testtrac-0.12.5/ticket/7">Ticket #7</a>
                       <span class="status">(new defect)</span>
                   </h1>
                   """),
            (200, u""), # post
        ])

        self.app.run(args)
        self.assertEquals(self.app.output, ['Current status: new'])

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

    def test_run_search(self):
        args = DummyArgs("search", ["something"])
        self.app.set_responses([
            (200, u"""random stuff before
                      <div>
                      <dl id="results">
                          <dt><a href="/any-random-project/ticket/7" class="searchable"><span class="new">#7</span>: defect: just something (new)</a></dt>
                          <dd class="searchable">just something</dd>
                          <dd>
                              <span class="author">By testuser</span> -
                              <span class="date">08/13/2013 19:06:10</span>
                          </dd>
                          <dt><a href="/any-random-project/ticket/6" class="searchable"><span class="new">#6</span>: defect: something is fishy (new)</a></dt>
                          <dd class="searchable">something is fishy</dd>
                          <dd>
                              <span class="author">By testuser</span> -
                              <span class="date">08/13/2013 19:06:00</span>
                          </dd>
                      </dl>
                      </div>""")
        ])

        self.app.run(args)
        self.assertEquals(self.app.output, [
            '#7. defect: just something (new)',
            '#6. defect: something is fishy (new)',
        ])
