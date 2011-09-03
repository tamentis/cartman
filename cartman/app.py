#!/usr/bin/env python

import csv
import sys
import re
import os
import json
import urllib
import requests
import difflib
import StringIO
import tempfile
import webbrowser
import email.parser
import ConfigParser

import exceptions
import ticket


CONFIG_LOCATIONS = [
    os.path.expanduser("~/.cartmanrc"),
    "/etc/cartmanrc",
]


class CartmanApp:

    """
    Ze *cartman* application class. All the commands starting with run_ are
    exposed to the command-line.
    """

    def __init__(self):
        self._read_config()
        self.session = requests.session(auth=(self.username, self.password))
        self.logged_in = False

    def _read_config(self):
        cp = ConfigParser.ConfigParser()
        cp.read(CONFIG_LOCATIONS)

        self.base_url = cp.get("trac", "base_url")
        self.username = cp.get("trac", "username")
        self.password = cp.get("trac", "password")
        self.required_fields = ["To", "Milestone", "Component", "Subject"]
        self.default_fields = ["To", "Cc", "Subject", "Component", "Milestone"]

    def _underline(self, text):
        """Given a string, return a series of dash with the same length.
        
        :param text: Text used as reference to create a line of len(text)
                     dashes.
        """
        return "-" * len(text)

    def _title(self, text):
        """Returns the same string with a line of dashes of the same size.

        :param text: Text to return underlined.
        """

        return text + "\n" + self._underline(text)

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
        token = "var properties="
        lines = [l for l in self.get("/query").content.splitlines() if token in l]

        if not lines:
            return {}

        line = (
            lines.pop()
                 .replace(token, "")
                 .replace(";","")
        )

        return json.loads(line)

    def _fuzzy_find(self, value, options):
        """Given a value and a list of options, find the one option that should
        be the closest match. We first use Python's ``difflib`` to find
        potential typos in exact matches, then we do a word-match using regular
        expressions.

        :param value: User-entered words.
        :param options: List of real, system understood values.

        """
        value = value.lower()
        options = {opt.lower(): opt for opt in options}

        matches = difflib.get_close_matches(value, options.keys())

        if not matches:
            for l_opt, opt in options.items():
                pattern = r".*\b%s\b.*" % value
                if re.match(pattern, l_opt):
                    matches.append(l_opt)

        if len(matches) == 1:
            return options[matches.pop()]

        return None

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
        This will allow Trac to generate the cookies that will be store on our
        ``self.session`` object.

        """
        if self.logged_in:
            return

        r = self.get("/")

        if r.status_code not in (200, 302):
            raise exceptions.LoginError("login failed")

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

    # TODO fix indent on doc strings..
    def print_commands(self):
        """Initial attempt to return a help screen with all the commands."""
        for attrname in dir(self):
            if attrname.startswith("run_"):
                func_name = attrname[4:]
                print(self._title(func_name))
                print(getattr(self, attrname).__doc__)
                print("")

    def open_in_browser(self, ticket_id):
        """Open the default web browser on the ticket page.

        :param ticket_id: id of the ticket to open in browser.

        """
        webbrowser.open(self.base_url + "/ticket/%d" % ticket_id)

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

    def run(self, options, args):
        """Main function called, convert the options and arguments into a
        function call within this instance.

        :param options: Options returned from the optparse module.
        :param args: Arguments returned from the optparse module.

        """
        self.open_after = options.open_after

        if args:
            command = args.pop(0)
        else:
            command = "default"

        func_name = "run_" + command
        if hasattr(self, func_name):
            getattr(self, func_name)(*args)
        else:
            raise exceptions.UnknownCommand("Unknown command: " + command)

    def run_report(self, report_id):
        """List tickets from a given report number.

        usage: cm report ticket_id

        """
        try:
            report_id = int(report_id)
        except ValueError:
            raise exceptions.InvalidParameter("report_id should be an integer")

        query_string = "/report/%d?format=tab" % report_id

        for t in self.get_tickets(query_string):
            print(t.format_title())

    def run_view(self, ticket_id):
        """Display a ticket summary.

        usage: cm view ticket_id

        """
        try:
            ticket_id = int(ticket_id)
        except ValueError:
            raise exceptions.InvalidParameter("ticket_id should be an integer")

        query_string = "/ticket/%d?format=tab" % ticket_id

        t = self.get_tickets(query_string).next()
        title = t.format_title()

        print(self._title(title))
        print("")

        print(t.description)

    def run_open(self, ticket_id):
        """Open a ticket in your browser.

        usage: cm open ticket_id
        """
        try:
            ticket_id = int(ticket_id)
        except ValueError:
            raise exceptions.InvalidParameter("ticket_id should be an integer")

        self.open_in_browser(ticket_id)

    def run_properties(self):
        """Lists the system's properties (Milestone, Component, etc.).

        usage: cm properties

        """
        properties = self._get_properties()

        print(self._title("Milestones"))
        print(", ".join(properties["milestone"]["options"]) + "\n")

        print(self._title("Components"))
        print(", ".join(properties["component"]["options"]) + "\n")


    def run_new(self, owner=None):
        """Create a new ticket.

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

        properties = self._get_properties()

        while not valid:
            # Assume the user will produce a valid ticket
            valid = True

            # Load the current values in a temp file for editing
            (fd, filename) = tempfile.mkstemp(suffix=".cm.ticket")
            fp = os.fdopen(fd, "w")
            fp.write(self._format_headers(headers))
            fp.write("\n\n")
            fp.write(body)
            fp.close()
            os.system("$EDITOR '%s'" % filename)

            # Use the email parser to get the headers.
            ep = email.parser.Parser()
            with open(filename, "r") as fp:
                em = ep.parse(fp)

            os.unlink(filename)

            body = em.get_payload()
            headers.update(em)

            errors = []
            fuzzy_match_fields = ("Milestone", "Component", "Type", "Version")

            for key in self.required_fields:
                if key in fuzzy_match_fields:
                    continue
                if not headers[key] or "**ERROR**" in headers[key]:
                    errors.append("Invalid '%s': cannot be blank" % key)

            for key in fuzzy_match_fields:
                valid_options = properties[key.lower()]["options"]

                if headers[key] not in valid_options:
                    m = self._fuzzy_find(headers[key], valid_options)
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
                    raw_input("\n-- Hit Enter to return to editor, ^C to abort --\n")
                except KeyboardInterrupt:
                    raise exceptions.FatalError("Ticket creation interrupted")

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

