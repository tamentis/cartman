# Copyright (c) 2011 Bertrand Janin <b@janin.com>
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
import StringIO
import tempfile
import webbrowser
import email.parser
import ConfigParser

import exceptions
import ticket
import ui
import text


CONFIG_LOCATIONS = [
    os.path.expanduser("~/.cartmanrc"),
    "/etc/cartmanrc",
]

MIN_TRAC_VERSION = (0, 12, 0)
MAX_TRAC_VERSION = (0, 13, 0)


class CartmanApp:

    """
    Ze *cartman* application class. All the commands starting with run_ are
    exposed to the command-line.
    """

    def __init__(self):
        self.site = "trac"
        self.logged_in = False
        self.browser = webbrowser

    def _read_config(self):
        cp = ConfigParser.ConfigParser()
        cp.read(CONFIG_LOCATIONS)

        self.base_url = cp.get(self.site, "base_url", "localhost")
        self.username = cp.get(self.site, "username", "cartman")
        self.password = cp.get(self.site, "password", "cartman")
        self.required_fields = ["To", "Milestone", "Component", "Subject",
                "Priority"]
        self.default_fields = ["To", "Cc", "Subject", "Component", "Milestone"]

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
        return text.extract_properties(self.get("/query").content)

    def _check_version(self):
        if self.trac_version < MIN_TRAC_VERSION \
                or self.trac_version >= MAX_TRAC_VERSION:
            version = ".".join([str(tok) for tok in self.trac_version])
            print("WARNING: Untested Trac version (%s)" % version)

    def _editor(self, filename):
        os.system("$EDITOR '%s'" % filename)

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
        if r.status_code != 302:
            r = self.get("/")

        if r.status_code not in (200, 302):
            raise exceptions.LoginError("login failed on %s" % r.request.url)

        # Grab the Trac version number, and throw a warning if not 0.12.
        self.trac_version = text.extract_trac_version(r.content)
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
        buf = StringIO.StringIO(r.content)
        return csv.DictReader(buf, delimiter="\t")

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

    # TODO fix indent on doc strings..
    def print_commands(self):
        """Initial attempt to return a help screen with all the commands."""
        for attrname in dir(self):
            if attrname.startswith("run_"):
                self.print_function_help(attrname)
                print("")

    def open_in_browser(self, ticket_id):
        """Open the default web browser on the ticket page.

        :param ticket_id: id of the ticket to open in browser.

        """
        self.browser.open(self.base_url + "/ticket/%d" % ticket_id)

    def open_in_browser_on_request(self, ticket_id):
        """Open the default web browser on the ticket page, only if
        ``self.open_after`` is set.

        :param ticket_id: id of the ticket to open in browser.

        """
        if self.open_after:
            self.open_in_browser(ticket_id)

    def _format_headers(self, headers):
        """Format the ticket header for the template in the order given in
        ``default_fields``, one per line using the email header syntax.

        :param headers: Dictionary of headers to format.

        """
        sort_ref = self.default_fields + headers.keys()
        pairs = headers.iteritems()
        pairs = ((k, v) for k, v in pairs if k in self.default_fields or v)
        pairs = sorted(pairs, key=lambda pair: sort_ref.index(pair[0]))
        return "\n".join([": ".join(pair) for pair in pairs])

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

        self._read_config()
        self.session = requests.session(auth=(self.username, self.password))

        func_name = "run_" + args.command
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            if "help" in args.parameters:
                self.print_function_help(func_name)
                return

            try:
                func(*args.parameters)
            except exceptions.InvalidParameter, ex:
                print("error: %s\n" % ex)
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
        else:
            raise exceptions.UnknownCommand("unknown command: " + func_name)

    def run_report(self, report_id=None):
        """List tickets from a given report number.

        usage: cm report ticket_id

        """
        report_id = text.validate_id(report_id)

        query_string = "/report/%d?format=tab" % report_id

        for t in self.get_tickets(query_string):
            print(t.format_title())

    def run_reports(self):
        """List reports available in the system.

        usage: cm reports

        """
        for d in self.get_dicts("/report?format=tab"):
            print("#%(report)s. %(title)s" % d)

    def run_view(self, ticket_id):
        """Display a ticket summary.

        usage: cm view ticket_id

        """
        ticket_id = text.validate_id(ticket_id)

        query_string = "/ticket/%d?format=tab" % ticket_id

        t = self.get_tickets(query_string).next()
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

    def _read_comment(self):
        """Prompt for a piece of text via the current EDITOR. Returns a string.
        """
        (fd, filename) = tempfile.mkstemp(suffix=".cm.ticket")
        self._editor(filename)
        with open(filename) as fp:
            comment = fp.read()
        return comment

    def run_comment(self, ticket_id):
        """Add a comment to the given ticket_id. This command does not return
        anything if successful. Command is cancelled if the content of the
        comment is empty.

        usage: cm comment ticket_id

        """
        ticket_id = text.validate_id(ticket_id)

        self.login()

        # Load the initial timestamp from the ticket page
        r = self.get("/ticket/%d" % ticket_id)
        timestamp = text.extract_timestamp(r.content)

        if self.message:
            comment = self.message
        else:
            comment = self._read_comment()

        if not comment.strip():
            raise exceptions.FatalError("empty comment, cancelling")

        r = self.post("/ticket/%d" % ticket_id, {
            "ts": timestamp,
            "comment": comment,
            "action": "leave",
        })

        if "system-message" in r.content or r.status_code != 200:
            raise exceptions.FatalError("unable to save comment")

    def run_status(self, ticket_id, status=None):
        """Updates the status of a ticket.

        usage: cm status ticket_id [new_status]

        """
        ticket_id = text.validate_id(ticket_id)

        self.login()

        # Get all the available actions for this ticket
        r = self.get("/ticket/%d" % ticket_id)
        timestamp = text.extract_timestamp(r.content)
        statuses = text.extract_statuses(r.content)

        # A ``status`` was provided, try to find the exact match, else just
        # display the current status for this ticket, and the available ones.
        if status:
            status = text.fuzzy_find(status, statuses)

            if not status:
                raise exceptions.FatalError("bad status (for this ticket: %s)" % \
                                        ", ".join(statuses))
        else:
            status = text.extract_status_from_ticket_page(r.content)
            print("Current status: %s" % status)
            print("Available statuses: %s" % ", ".join(statuses))
            return

        if self.message:
            comment = self.message
        elif self.add_comment:
            comment = self._read_comment()
        else:
            comment = ""

        r = self.post("/ticket/%d" % ticket_id, {
            "ts": timestamp,
            "action": status,
            "comment": comment,
        })

        if "system-message" in r.content or r.status_code != 200:
            raise exceptions.FatalError("unable to set status")

    def run_new(self, owner=None):
        """Create a new ticket and return its id if successful.

        usage: cm new [owner]

        """
        owner = owner or self.username

        self.login()

        valid = False
        headers = {
            "Subject": "",
            "To": owner,
            "Cc": "",
            "Milestone": "",
            "Component": "",
            "Priority": "2",
            "Type": "defect",
            "Keywords": "",
            "Version": "",
        }
        body = "\n"

        while not valid:
            # Get the properties at each iteration, in case an admin updated
            # the list in the mean time, especially because of this new ticket.
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
            headers.update(em)

            errors = []
            fuzzy_match_fields = ("Milestone", "Component", "Type", "Version",
                                  "Priority")

            # Ensures all the required fields are filled-in
            for key in self.required_fields:
                if key in fuzzy_match_fields:
                    continue
                if not headers[key] or "**ERROR**" in headers[key]:
                    errors.append("Invalid '%s': cannot be blank" % key)

            # Some fields are tolerant to incomplete values, this is where we
            # try to complete them.
            for key in fuzzy_match_fields:
                valid_options = properties[key.lower()]["options"]

                if headers[key] not in valid_options:
                    m = text.fuzzy_find(headers[key], valid_options)
                    if m:
                        headers[key] = m
                    else:
                        if key in self.required_fields:
                            errors.append("Invalid '%s': expected: %s" % \
                                        (key, ", ".join(valid_options)))
                        else:
                            headers[key] = ""

            if errors:
                valid = False
                print("\nFound the following errors:")
                for error in errors:
                    print(" - %s" % error)

                try:
                    self._input("\n-- Hit Enter to return to editor, "\
                              "^C to abort --\n")
                except KeyboardInterrupt:
                    raise exceptions.FatalError("ticket creation interrupted")

        r = self.post("/newticket", {
            "field_summary": headers["Subject"],
            "field_type": headers["Type"],
            "field_version": headers["Version"],
            "field_description": body,
            "field_milestone": headers["Milestone"],
            "field_component": headers["Component"],
            "field_owner": headers["To"],
            "field_keywords": headers["Keywords"],
            "field_cc": headers["Cc"],
            "field_attachment": "",
        })

        if r.status_code != 200:
            raise exceptions.RequestException("unable to create new ticket.")

        try:
            ticket_id = int(r.url.split("/")[-1])
        except:
            raise exceptions.RequestException("returned ticket_id is invalid.")

        self.open_in_browser_on_request(ticket_id)
        print("ticket #%d created" % ticket_id)

