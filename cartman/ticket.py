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


# This dictionary is used to translate different properties from the tab
# delimited files to instance properties.
TRANSLATIONS = {
    "component": "component",
    "description": "description",
    "id": "id",
    "milestone": "milestone",
    "owner": "owner",
    "reporter": "reporter",
    "_reporter": "reporter",
    "resolution": "resolution",
    "status": "status",
    "summary": "summary",
    "ticket": "id",
    "type": "type",
    "version": "version",
}

# Any of these types will need casting.
TYPES = {
    "id": int,
}


class Ticket(object):

    def __init__(self):
        self.id = 0
        self.type = "N/A"
        self.summary = "N/A"
        self.reporter = "N/A"
        self.description = "N/A"
        self.milestone = "N/A"
        self.status = "unknown"
        self.owner = "unknown"
        self.resolution = ""
        self.version = ""

    def format_id(self):
        return "#{}.".format(self.id)

    def format_title(self):
        return "{id_fmt} {summary} ({reporter})".format(
            id_fmt = self.format_id(),
            summary = self.summary,
            reporter = self.reporter,
        )

def factory(ticket_dict):
    """Create a new ticket and copy the properties from a dictionary, with a
    few rules regarding translation and type casting.

    :param ticket_dict: Dictionary as returned from the Trac system, typically
                        translated from a tab-delimited format by cartman.
    """
    ticket = Ticket()

    for src_name, dest_name in TRANSLATIONS.items():
        if src_name in ticket_dict:
            if dest_name in TYPES and TYPES[dest_name] == int:
                value = int(ticket_dict[src_name])
            else:
                value = ticket_dict[src_name]

            setattr(ticket, dest_name, value)

    return ticket
