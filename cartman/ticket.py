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


class Ticket:

    def __init__(self):
        self.id = 0
        self.summary = "Summary N/A"
        self.reporter = "Reporter N/A"
        self.description = "Description N/A"

    def format_id(self):
        return "#%d." % self.id

    def format_title(self):
        return "%(id_fmt)s %(summary)s (%(reporter)s)" % {
            "id_fmt": self.format_id(),
            "summary": self.summary,
            "reporter": self.reporter,
        }


def factory(ticket_dict):
    ticket = Ticket()

    if "id" in ticket_dict:
        ticket.id = int(ticket_dict["id"])
    elif "ticket" in ticket_dict:
        ticket.id = int(ticket_dict["ticket"])

    if "summary" in ticket_dict:
        ticket.summary = ticket_dict["summary"]

    if "_reporter" in ticket_dict:
        ticket.reporter = ticket_dict["_reporter"]
    elif "reporter" in ticket_dict:
        ticket.reporter = ticket_dict["reporter"]

    if "description" in ticket_dict:
        ticket.description = ticket_dict["description"]

    return ticket
