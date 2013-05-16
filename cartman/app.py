# Copyright (c) 2011-2013 Bertrand Janin <b@janin.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import csv
import os
import requests
import tempfile
import webbrowser
import email.parser
from collections import OrderedDict

from cartman.compat import configparser
from cartman import exceptions
from cartman import ticket
from cartman import ui
from cartman import text


CONFIG_LOCATIONS = [
    os.path.expanduser("~/.cartman/config"),
    "/etc/cartmanrc",
]

MIN_TRAC_VERSION = (0, 11)
MAX_TRAC_VERSION = (1, 0)

AUTH_TYPES = {'basic': requests.auth.HTTPBasicAuth,
              'digest': requests.auth.HTTPDigestAuth}

DEFAULT_TEMPLATE = """To:
Cc:
Milestone:
Component:
Priority: major
Type: defect
Keywords:
Version:
Subject:

"""


class CartmanApp(object):

    """
    Application class. All the commands starting with run_ are exposed to the
    command-line.
    """

    def __init__(self):
        self.site = "trac"
        self.logged_in = False
        self.browser = webbrowser

    def _read_config(self):
        defaults = {
            "auth_type": "basic",
            "verify_ssl_cert": "true"
        }

        cp = configparser.RawConfigParser(defaults)
        cp.read(CONFIG_LOCATIONS)

        self.base_url = cp.get(self.site, "base_url")
        self.username = cp.get(self.site, "username")
        self.password = cp.get(self.site, "password")
        self.verify_ssl_cert = cp.getboolean(self.site, "verify_ssl_cert")

        # load auth
        auth_type = cp.get(self.site, "auth_type")
        auth_type = auth_type.lower()
        if auth_type not in AUTH_TYPES:
            msg = ("Invalid auth setting: {}. Allowed auth_type values are: {}"
                   .format(auth_type, ', '.join(sorted(AUTH_TYPES.keys()))))
            raise exceptions.InvalidConfigSetting(msg)
        self.auth_type = auth_type

        self.required_fields = ["To", "Component", "Subject", "Priority"]

    def _get_form_token(self):
        """Return the form_token sent on all the POST forms for validation.
        This value is store as a cookie, on the session. If the specifically
        named cookie is not found, returns an empty string.

        """
        for cookie in self.session.cookies:
            if cookie.name == "trac_form_token":
                return cookie.value

        return ""

    def _get_properties(self):
        """Return all the values typically used in drop-downs on the create
        ticket page, such as Milestones, Versions, etc. These lists are
        extracted from the JavaScript dictionary exposed on the query page.

        """
        return text.extract_properties(self.get("/query").text)

    def _check_version(self):
        if self.trac_version < MIN_TRAC_VERSION \
                or self.trac_version > MAX_TRAC_VERSION:
            version = ".".join([str(tok) for tok in self.trac_version])
            print("WARNING: Untested Trac version ({})".format(version))

    def _editor(self, filename):
        os.system("$EDITOR '{}'".format(filename))

    def _input(self, prompt):
        return raw_input(prompt)

    def get(self, query_string, data=None):
        """Generates a GET query on the target Trac system.

        :param query_string: Starts with a slash, part of the URL between the
                             domain and the parameters (before the ?).
        :param data: Dictionary of parameters to encode at the end of the
                     ``query_string``.
        """
        return self.session.get(self.base_url + query_string, data=data)

    def post(self, query_string, data=None):
        """Generates a POST query on the target Trac system. This also alters
        the given data to include the form token stored on the cookies. Without
        this token, Trac will refuse form submissions.

        :param query_string: Starts with a slash, part of the URL between the
                             domain and the parameters (before the ?).
        :param data: Dictionary of parameters to encode and transmit to the
                     target page.
        """
        if data:
            data["__FORM_TOKEN"] = self._get_form_token()
        return self.session.post(self.base_url + query_string, data=data)

    def login(self):
        """Ensure the current session is logged-in, accessing the main page.
        This will allow Trac to generate the cookies that will be stored on our
        ``self.session`` object.

        """
        if self.logged_in:
            return

        # Seems that depending on the method used to serve trac, we need to use
        # a different path to initiate authentication.
        r = self.get("/login")

        if r.status_code == 401:
            msg = ("login failed on {}. You might be using wrong "
                   "username/password combo or wrong auth type"
                   .format(r.request.url))
            raise exceptions.LoginError(msg)

        if r.status_code != 302:
            r = self.get("/")

        if r.status_code not in (200, 302):
            raise exceptions.LoginError("login failed on {}"
                                        .format(r.request.url))

        # Grab the Trac version number, and throw a warning if not 0.12.
        self.trac_version = text.extract_trac_version(r.text)
        self._check_version()

        self.logged_in = True

    def get_dicts(self, query_string):
        """Wrapper around the ``get`` method that ensures we are logged-in and
        converts the returned data to dictionaries, assuming the query
        originally returns tab-delimited raw data.

        :param query_string: Starts with a slash, part of the URL between the
                             domain and the parameters (before the ?).
        """

        self.login()
        r = self.get(query_string)
        data = r.content

        # Recent version of Trac seem to be sending data with a BOM (?!)
        if data[0] == u'\ufeff':
            data = data[1:]

        return csv.DictReader(data.splitlines(True), delimiter="\t")

    def get_tickets(self, query_string):
        """Wrapper around the ``get_dicts`` method that converts the
        dictionaries into ``Ticket`` instances.

        :param query_string: Starts with a slash, part of the URL between the
                             domain and the parameters (before the ?).
        """
        for ticket_dict in self.get_dicts(query_string):
            yield ticket.factory(ticket_dict)

    def print_function_help(self, attrname):
        """Print the docstring for one function.

        :param attrname: Name of the function, with the run_ prefix.

        """
        func_name = attrname[4:]
        print(ui.title(func_name))
        print(getattr(self, attrname).__doc__)

    def list_commands(self):
        """Return list of all the commands."""
        commands = []
        for attrname in dir(self):
            if attrname.startswith("run_"):
                commands.append(attrname)
        return commands

    def print_commands_list(self):
        """Print command list minus help."""
        print("Available Commands:\n")
        for command_name in self.list_commands():
            if command_name != "run_help":
                print(" "*8 + command_name[4:])
        print("")

    # TODO fix indent on doc strings..
    def print_commands(self):
        """Initial attempt to return a help screen with all the commands."""
        for command_name in self.list_commands():
            self.print_function_help(command_name)
            print("")

    def open_in_browser(self, ticket_id):
        """Open the default web browser on the ticket page.

        :param ticket_id: id of the ticket to open in browser.

        """
        self.browser.open("{}/ticket/{}".format(self.base_url, ticket_id))

    def open_in_browser_on_request(self, ticket_id):
        """Open the default web browser on the ticket page, only if
        ``self.open_after`` is set.

        :param ticket_id: id of the ticket to open in browser.

        """
        if self.open_after:
            self.open_in_browser(ticket_id)

    def resolve_template(self):
        """Pick up the specified or default template, if any.

        This method returns the content of the template. It first looks for a
        template specified in the command line with the ``-t`` flag. If none
        was specified it returns the content of the ``default`` template. If no
        ``default`` template exist, it will return None.

        """
        templates_path = os.path.join("~", ".cartman", "templates")
        templates_path = os.path.expanduser(templates_path)

        if self.template:
            path = os.path.join(templates_path, self.template)
        else:
            path = os.path.join(templates_path, "default")
            if not os.path.exists(path):
                return None

        # If the template does not exist, let the exception escalate and crash
        # the whole app. The error messages are typically explicit enough.
        with open(path) as fp:
            template = fp.read()

        return template

    def _format_headers(self, headers):
        """Format the ticket header for the template, one per line using the
        email header syntax.

        :param headers: Dictionary of headers to format.

        """
        return "\n".join([": ".join(pair) for pair in headers.items()])

    def run(self, args):
        """Main function called, convert the options and arguments into a
        function call within this instance.

        :param options: Options returned from the optparse module.
        :param args: Arguments returned from the optparse module.

        """
        self.site = args.site or self.site
        self.open_after = args.open_after
        self.add_comment = args.add_comment
        self.message = args.message
        self.template = args.template

        self._read_config()
        self.session = requests.session()

        auth_class = AUTH_TYPES[self.auth_type]
        self.session.auth = auth_class(self.username, self.password)
        self.session.verify = self.verify_ssl_cert

        func_name = "run_" + args.command
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            if "help" in args.parameters:
                self.print_function_help(func_name)
                return

            try:
                func(*args.parameters)
            except exceptions.InvalidParameter as ex:
                print("error: {}\n".format(ex))
                self.print_function_help(func_name)
                return
        else:
            raise exceptions.UnknownCommand("unknown command: " + args.command)

    def run_help(self, command="help"):
        """Show the help for a given command.

        usage: cm help command

        """
        func_name = "run_" + command
        if hasattr(self, func_name):
            self.print_function_help(func_name)
            if command == "help":
                self.print_commands_list()
        else:
            raise exceptions.UnknownCommand("unknown command: " + func_name)

    def run_report(self, report_id=None):
        """List tickets from a given report number.

        usage: cm report ticket_id

        """
        report_id = text.validate_id(report_id)

        query_string = "/report/{}?format=tab".format(report_id)

        for t in self.get_tickets(query_string):
            print(t.format_title())

    def run_reports(self):
        """List reports available in the system.

        usage: cm reports

        """
        for d in self.get_dicts("/report?format=tab"):
            print("#{report}. {title}".format(**d))

    def run_view(self, ticket_id):
        """Display a ticket summary.

        usage: cm view ticket_id

        """
        ticket_id = text.validate_id(ticket_id)

        query_string = "/ticket/{}?format=tab".format(ticket_id)

        t = next(self.get_tickets(query_string))
        title = t.format_title()

        print(ui.title(title))
        print("")

        print(t.description)

    def run_open(self, ticket_id):
        """Open a ticket in your browser.

        usage: cm open ticket_id
        """
        ticket_id = text.validate_id(ticket_id)

        self.open_in_browser(ticket_id)

    def run_properties(self):
        """Lists the system's properties (Milestone, Component, etc.).

        usage: cm properties

        """
        properties = self._get_properties()

        print(ui.title("Milestones"))
        print(", ".join(properties["milestone"]["options"]) + "\n")

        print(ui.title("Components"))
        print(", ".join(properties["component"]["options"]) + "\n")

        print(ui.title("Status"))
        print(", ".join(properties["status"]["options"]) + "\n")

        print(ui.title("Priority"))
        print(", ".join(properties["priority"]["options"]) + "\n")

    def _read_comment(self):
        """Prompt for a piece of text via the current EDITOR. Returns a string.
        """
        (fd, filename) = tempfile.mkstemp(suffix=".cm.ticket")
        self._editor(filename)
        with open(filename) as fp:
            comment = fp.read()
        return comment

    def _extract_timestamps(self, raw_html):
        """Wrapper around extract_time_v0 and extract_time_v1."""
        if self.trac_version >= (1, 0):
            return text.extract_timestamps_v1(raw_html)
        else:
            return text.extract_timestamps_v0(raw_html)

    def run_comment(self, ticket_id):
        """Add a comment to the given ticket_id. This command does not return
        anything if successful. Command is cancelled if the content of the
        comment is empty.

        usage: cm comment ticket_id

        """
        ticket_id = text.validate_id(ticket_id)

        self.login()

        # Load the timestamps from the ticket page.
        r = self.get("/ticket/{}".format(ticket_id))
        timestamps = self._extract_timestamps(r.text)

        if self.message:
            comment = self.message
        else:
            comment = self._read_comment()

        if not comment.strip():
            raise exceptions.FatalError("empty comment, cancelling")

        data = {
            "comment": comment,
            "action": "leave",
            "submit": "Submit changes",
        }
        data.update(timestamps)

        r = self.post("/ticket/{}".format(ticket_id), data)

        # Starting from 1.0+, the system-message element is always on the page,
        # only the style is changed.
        if self.trac_version >= (1, 0):
            token = 'system-message" style=""'
        else:
            token = 'system-message'

        if token in r.text or r.status_code != 200:
            raise exceptions.FatalError("unable to save comment")

    def run_status(self, ticket_id, status=None):
        """Updates the status of a ticket.

        usage: cm status ticket_id [new_status]

        """
        ticket_id = text.validate_id(ticket_id)

        self.login()

        # Get all the available actions for this ticket
        r = self.get("/ticket/{}".format(ticket_id))
        timestamps = self._extract_timestamps(r.text)
        statuses = text.extract_statuses(r.text)

        # A ``status`` was provided, try to find the exact match, else just
        # display the current status for this ticket, and the available ones.
        if status:
            status = text.fuzzy_find(status, statuses)

            if not status:
                raise exceptions.FatalError("bad status (for this ticket: {})"
                                            .format(", ".join(statuses)))
        else:
            status = text.extract_status_from_ticket_page(r.text)
            print("Current status: {}".format(status))
            print("Available statuses: {}".format(", ".join(statuses)))
            return

        if self.message:
            comment = self.message
        elif self.add_comment:
            comment = self._read_comment()
        else:
            comment = ""

        data = {
            "action": status,
            "comment": comment,
        }
        data.update(timestamps)

        r = self.post("/ticket/{}".format(ticket_id), data)

        if "system-message" in r.text or r.status_code != 200:
            raise exceptions.FatalError("unable to set status")

    def run_new(self, owner=None):
        """Create a new ticket and return its id if successful.

        usage: cm new [owner]

        """
        self.login()

        template = self.resolve_template()

        if not template:
            template = DEFAULT_TEMPLATE

        # Parse the template ahead of time, allowing us to insert the Owner/To.
        ep = email.parser.Parser()
        em = ep.parsestr(template)
        body = em.get_payload()
        headers = OrderedDict(em.items())

        # The owner specified on the command line always prevails.
        if owner:
            headers["To"] = owner

        # If all else fail, assign it to yourself.
        if not headers["To"]:
            headers["To"] = self.username

        valid = False
        while not valid:
            # Get the properties at each iteration, in case an admin updated
            # the list in the mean time.
            properties = self._get_properties()

            # Assume the user will produce a valid ticket
            valid = True

            # Load the current values in a temp file for editing
            (fd, filename) = tempfile.mkstemp(suffix=".cm.ticket")
            fp = os.fdopen(fd, "w")

            fp.write(self._format_headers(headers))
            fp.write("\n\n")
            fp.write(body)

            fp.close()
            self._editor(filename)

            # Use the email parser to get the headers.
            ep = email.parser.Parser()
            with open(filename, "r") as fp:
                em = ep.parse(fp)

            os.unlink(filename)

            body = em.get_payload()
            headers = OrderedDict(em.items())

            errors = []
            fuzzy_match_fields = ("Milestone", "Component", "Type", "Version",
                                  "Priority")

            # Ensures all the required fields are filled-in
            for key in self.required_fields:
                if key in fuzzy_match_fields:
                    continue
                if not headers.get(key) or "**ERROR**" in headers[key]:
                    errors.append("Invalid '{}': cannot be blank".format(key))

            # Some fields are tolerant to incomplete values, this is where we
            # try to complete them.
            for key in fuzzy_match_fields:
                lkey = key.lower()
                if lkey not in properties:
                    continue

                valid_options = properties[lkey]["options"]

                # The specified value is not available in the multi-choice.
                if key in headers and headers[key] not in valid_options:
                    m = text.fuzzy_find(headers[key], valid_options)
                    if m:
                        # We found a close match, update the value with it.
                        headers[key] = m
                    else:
                        # We didn't find a close match. If the user entered
                        # something explicitly or if this field is required,
                        # this is an error, else just wipe the value and move
                        # on.
                        if headers[key] or key in self.required_fields:
                            joined_options = ", ".join(valid_options)
                            errors.append(u"Invalid '{}': expected: {}"
                                          .format(key, joined_options))
                        else:
                            headers[key] = ""

            if errors:
                valid = False
                print("\nFound the following errors:")
                for error in errors:
                    print(u" - {}".format(error))

                try:
                    self._input("\n-- Hit Enter to return to editor, "\
                              "^C to abort --\n")
                except KeyboardInterrupt:
                    raise exceptions.FatalError("ticket creation interrupted")

        # Since the body is expected to be using CRLF line termination, we
        # replace newlines by CRLF if no CRLF is found.
        if "\r\n" not in body:
            body = body.replace("\n", "\r\n")

        fields_data = {
            "field_summary": headers.get("Subject", ""),
            "field_type": headers.get("Type", ""),
            "field_version": headers.get("Version", ""),
            "field_description": body,
            "field_milestone": headers.get("Milestone", ""),
            "field_component": headers.get("Component", ""),
            "field_owner": headers.get("To", ""),
            "field_keywords": headers.get("Keywords", ""),
            "field_cc": headers.get("Cc", ""),
            "field_attachment": "",
        }

        # Assume anything outside of the original headers it to be included as
        # fields.
        for key, value in headers.items():
            field_name = "field_" + key.lower()
            if field_name not in fields_data:
                fields_data[field_name] = value

        r = self.post("/newticket", fields_data)

        if r.status_code != 200:
            raise exceptions.RequestException("unable to create new ticket.")

        try:
            ticket_id = int(r.url.split("/")[-1])
        except:
            raise exceptions.RequestException("returned ticket_id is invalid.")

        self.open_in_browser_on_request(ticket_id)
        print("ticket #{} created".format(ticket_id))
