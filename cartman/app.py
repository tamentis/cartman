#!/usr/bin/env python

import csv
import sys
import os
import email.parser
import urllib
import requests
import tempfile
import webbrowser
import ConfigParser

import exceptions
import ticket


CONFIG_LOCATIONS = [
    os.path.expanduser("~/.cartmanrc"),
    "/etc/cartmanrc",
]

TICKET_TEMPLATE = """To: %(To)s
Cc: %(Cc)s
Subject: %(Subject)s
Type: %(Type)s
Component: %(Component)s
Milestone: %(Milestone)s
Priority: %(Priority)s


"""


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

    def _underline(self, text):
        return "-" * len(text)

    def _get_form_token(self):
        """Return the form_token sent on all the POST forms for validation.
        This value is store as a cookie, on the session.

        """
        for cookie in self.session.cookies:
            if cookie.name == "trac_form_token":
                return cookie.value

        return ""

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
            raise LoginError("login failed")

    def dict_open(self, query_string):
        self.login()
        f = self.get(query_string)
        return csv.DictReader(f, delimiter="\t")

    def ticket_open(self, query_string):
        for ticket_dict in self.dict_open(query_string):
            yield ticket.factory(ticket_dict)

    # TODO fix indent on doc strings..
    def print_commands(self):
        for attrname in dir(self):
            if attrname.startswith("run_"):
                func_name = attrname[4:]
                print(func_name)
                print(self._underline(func_name))
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

        for t in self.ticket_open(query_string):
            print(t.format_title())

    def run_ticket(self, ticket_id):
        """Show a ticket, with its comments."""

        try:
            ticket_id = int(ticket_id)
        except ValueError:
            raise exceptions.InvalidParameter("ticket_id should be an integer")

        query_string = "/ticket/%d?format=tab" % ticket_id

        t = self.ticket_open(query_string).next()
        title = t.format_title()

        print(title)
        print(self._underline(title))
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

    def run_new(self):
        self.login()
        valid = False
        headers = {
            "Subject": "",
            "To": self.username,
            "Cc": "",
            "Milestone": "",
            "Component": "",
            "Priority": "2",
            "Type": "defect",
        }
        body = ""

        while not valid:
            # Assume the user will produce a valid ticket
            valid = True

            # Load the current values in a temp file for editing
            (fd, filename) = tempfile.mkstemp()
            fp = os.fdopen(fd, "w")
            fp.write(TICKET_TEMPLATE % headers)
            fp.write(body)
            fp.close()
            os.system("$EDITOR '%s'" % filename)

            # Use the email parser to get the headers.
            ep = email.parser.Parser()
            with open(filename, "r") as fp:
                em = ep.parse(fp)

            body = em.get_payload()
            headers.update(em)

            errors = []
             
            for key in ("Subject", "To"):
                if not headers[key] or "**ERROR**" in headers[key]:
                    errors.append("'%s' cannot be blank" % key)

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
            "field_summary": em["Subject"],
            "field_type": "defect",
            "field_version": "1.0",
            "field_description": "This is brilliant",
            "field_milestone": "milestone1",
            "field_component": "component1",
            "field_owner": "bjanin",
            "field_keywords": "",
            "field_cc": "",
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

