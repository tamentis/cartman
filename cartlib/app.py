#!/usr/bin/env python2.7

import csv
import sys
import os
import email.parser
import urllib
import urllib2
import tempfile
import webbrowser
import ConfigParser

import exceptions
import ticket


CONFIG_LOCATIONS = [
    os.path.expanduser("~/.cartmanrc"),
    "/etc/cartmanrc",
]

TICKET_TEMPLATE = """To: bjanin
Cc: 
Subject: 
Type: defect
Component:
Milestone:
Priority: 2


"""


class CartmanApp:
    
    def __init__(self):
        self._read_config()
        self._init_urllib()

    def _init_urllib(self):
        authinfo = urllib2.HTTPBasicAuthHandler()
        authinfo.add_password(realm=self.realm,
                uri=self.base_url + "/",
                user=self.username,
                passwd=self.password)

        opener = urllib2.build_opener(authinfo)
        urllib2.install_opener(opener)

    def _read_config(self):
        cp = ConfigParser.ConfigParser()
        cp.read(CONFIG_LOCATIONS)

        self.base_url = cp.get("trac", "base_url")
        self.realm = cp.get("trac", "realm")
        self.username = cp.get("trac", "username")
        self.password = cp.get("trac", "password")

    def _underline(self, text):
        return "-" * len(text)

    def raw_open(self, query_string, data=None):
        print(self.base_url + query_string)
        print(data)
        return urllib2.urlopen(self.base_url + query_string, data=data)

    def dict_open(self, query_string):
        f = self.raw_open(query_string)
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
        if args:
            command = args.pop(0)
        else:
            command = "default"

        func_name = "run_" + command
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            func(*args)
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

    def run_open(self, ticket_id):
        """Open a ticket in your browser."""

        try:
            ticket_id = int(ticket_id)
        except ValueError:
            raise exceptions.InvalidParameter("ticket_id should be an integer")

        webbrowser.open(self.base_url + "/ticket/%d" % ticket_id)

    def run_new(self):
        (fd, name) = tempfile.mkstemp()
        fp = os.fdopen(fd, "w")
        fp.write(TICKET_TEMPLATE)
        fp.close()
        os.system("$EDITOR \"%s\"" % name)

        ep = email.parser.Parser()
        with open(name, "r") as fp:
            em = ep.parse(fp)

        x = self.raw_open("/newticket")

        self.raw_open("/newticket", urllib.urlencode({
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
            "__FORM_TOKEN": "a83d76f29b1d51fd844a5465",
            "submit": "Create Ticket",
        }))

        import pdb; pdb.set_trace()
            
