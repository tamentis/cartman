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
        return "-" * len(text)

    def _title(self, text):
        return text + "\n" + self._underline(text)

    def _get_form_token(self):
        """Return the form_token sent on all the POST forms for validation.
        This value is store as a cookie, on the session.

        """
        for cookie in self.session.cookies:
            if cookie.name == "trac_form_token":
                return cookie.value

        return ""

    def _get_properties(self):
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
        value = value.lower()
        options = {opt.lower(): opt for opt in options}

        matches = difflib.get_close_matches(value, options.keys())

        if not matches:
            for l_opt, opt in options.items():
                pattern = r".*\b%s\b.*" % value
                if re.match(pattern, l_opt):
                    matches.append(opt)

        if len(matches) == 1:
            return matches.pop()

        return None

    def get(self, query_string, data=None):
        return self.session.get(self.base_url + query_string, data=data)

    def post(self, query_string, data=None):
        if data:
            data["__FORM_TOKEN"] = self._get_form_token()
        return self.session.post(self.base_url + query_string, data=data)

    def login(self):
        """Ensures the current session is logged-in."""
        if self.logged_in:
            return

        r = self.get("/login")

        if r.status_code not in (200, 302):
            raise exceptions.LoginError("login failed")

    def get_dicts(self, query_string):
        self.login()
        r = self.get(query_string)
        buf = StringIO.StringIO(r.content)
        return csv.DictReader(buf, delimiter="\t")

    def get_tickets(self, query_string):
        for ticket_dict in self.get_dicts(query_string):
            yield ticket.factory(ticket_dict)

    # TODO fix indent on doc strings..
    def print_commands(self):
        for attrname in dir(self):
            if attrname.startswith("run_"):
                func_name = attrname[4:]
                print(self._title(func_name))
                print(getattr(self, attrname).__doc__)
                print("")

    def run(self, options, args):
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
        """List tickets from a given report number."""

        try:
            report_id = int(report_id)
        except ValueError:
            raise exceptions.InvalidParameter("report_id should be an integer")

        query_string = "/report/%d?format=tab" % report_id

        for t in self.get_tickets(query_string):
            print(t.format_title())

    def run_ticket(self, ticket_id):
        """Show a ticket, with its comments."""

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

    def open_in_browser(self, ticket_id):
        webbrowser.open(self.base_url + "/ticket/%d" % ticket_id)

    def open_in_browser_on_request(self, ticket_id):
        if self.open_after:
            self.open_in_browser(ticket_id)

    def run_open(self, ticket_id):
        """Open a ticket in your browser."""

        try:
            ticket_id = int(ticket_id)
        except ValueError:
            raise exceptions.InvalidParameter("ticket_id should be an integer")

        self.open_in_browser(ticket)

    def _format_headers(self, headers):
        sort_ref = self.default_fields + headers.keys()
        pairs = headers.iteritems()
        pairs = ((k, v) for k, v in pairs if k in self.default_fields or v)
        pairs = sorted(pairs, key=lambda pair: sort_ref.index(pair[0]))
        return "\n".join([": ".join(pair) for pair in pairs])

    def run_properties(self):
        """Lists the system's properties (Milestone, Component, etc.)."""

        properties = self._get_properties()

        print(self._title("Milestones"))
        print(", ".join(properties["milestone"]["options"]) + "\n")

        print(self._title("Components"))
        print(", ".join(properties["component"]["options"]) + "\n")


    def run_new(self, owner=None):
        """Create a new ticket."""
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

