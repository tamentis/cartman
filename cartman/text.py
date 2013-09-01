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

"""
Various text processing functions.
"""

import re
import json
import difflib

from cartman import exceptions


re_version = re.compile(r"Trac (\d+)\.(\d+)", re.MULTILINE)
re_search_result = re.compile(r'<dt><a href="[^"]+" class="searchable">'
                              r'<span class="\w+">#(\d+)</span>'
                              r': ([^<]+)</a></dt>')
re_message = re.compile(r"<p class=\"message\">([^<]+)</p>")


def fuzzy_find(value, options):
    """Given a value and a list of options, find the one option that should
    be the closest match. We first use Python's ``difflib`` to find
    potential typos in exact matches, then we do a word-match using regular
    expressions.

    :param value: User-entered words.
    :param options: List of real, system understood values.

    """
    value = value.lower()
    options = {opt.lower(): opt for opt in options}

    if value in options.keys():
        return options[value]

    # If we have a single match on tokenized options, that's probably good
    # enough.
    tokenized_matches = []
    for key, option in options.items():
        tokens = key.split()
        if value in tokens:
            tokenized_matches.append(option)

    if len(tokenized_matches) == 1:
        return tokenized_matches[0]

    matches = difflib.get_close_matches(value, options.keys())

    if not matches:
        for l_opt, opt in options.items():
            pattern = r".*\b{}\b.*".format(value)
            if re.match(pattern, l_opt):
                matches.append(l_opt)

    if len(matches) == 1:
        return options[matches.pop()]

    return None


def validate_id(raw_value):
    """Ensures the given raw string is an int and returns it converted.

    :param raw_value: Entity id as a string or int.

    """
    try:
        converted_id = int(raw_value)
    except (ValueError, TypeError):
        raise exceptions.InvalidParameter(
                "invalid identifier (should be an int)")

    return converted_id


def extract_timestamps_common(token, raw_html):
    """Given a dump of HTML data, extract the timestamp and return it as a
    string value.

    :param raw_html: Dump from the ticket page.

    """
    regex = r"""name="{}" value="([^"]+)""".format(token)

    m = re.search(regex, raw_html, re.MULTILINE)

    if m:
        timestamp = m.group(1)
    else:
        raise exceptions.FatalError("unable to fetch timestamp")

    return timestamp


def extract_timestamps_v0(raw_html):
    return {
        "ts": extract_timestamps_common("ts", raw_html),
    }

def extract_timestamps_v1(raw_html):
    return {
        "start_time": extract_timestamps_common("start_time", raw_html),
        "view_time": extract_timestamps_common("view_time", raw_html),
    }


def extract_statuses(raw_html):
    """Given a dump of HTML data, extract the timestamp and return it as a
    string value.

    :param raw_html: Dump from the ticket page.

    """
    re_status = r'<input type="radio" [^<]+name="action" value="([^"]+)'
    return re.findall(re_status, raw_html)


def extract_status_from_ticket_page_common(re_status, raw_html):
    """Given a dump of the HTML ticket page, extract the current status of
    a ticket.

    TODO: return resolution and display it if any.

    :param raw_html: Dump for the ticket page.

    """
    m = re.search(re_status, raw_html, re.MULTILINE)

    if m:
        status = m.group(1)
        # task_type = m.group(2)
        # resolution = m.group(3)
    else:
        raise exceptions.FatalError("unable to fetch ticket status")

    return status


def extract_status_from_ticket_page_v0(raw_html):
    re_status = r'<span class="status">\((\w+) (\w+)(?:: (\w+))?\)</span>'
    return extract_status_from_ticket_page_common(re_status, raw_html)


def extract_status_from_ticket_page_v1(raw_html):
    re_status = r'<span class="trac-status">[\s\n]+<a href="[^"]+">(\w+)</a>'
    return extract_status_from_ticket_page_common(re_status, raw_html)


def extract_properties(raw_html):
    """Return all the values typically used in drop-downs on the create
    ticket page, such as Milestones, Versions, etc. These lists are
    extracted from the JavaScript dictionary exposed on the query page.

    :param raw_html: Dump from the query page.

    """
    re_prop = r"var properties=([^;]+)"
    prop_tokens = re.findall(re_prop, raw_html, re.MULTILINE)

    if len(prop_tokens) < 1:
        return {}

    return json.loads(prop_tokens[0])


def extract_trac_version(raw_html):
    """Returns a tuple of three values representing the current Trac version.

    :param raw_html: Dump from any page.

    """
    results = re_version.findall(raw_html)

    if not results:
        return ()

    major, minor = tuple([int(t) for t in results[0]])

    return (major, minor)


def extract_message(raw_html):
    """Returns the content of the message element.

    This element appears typically on pages with errors.

    :param raw_html: Dump from any page.

    """
    results = re_message.findall(raw_html)

    if results:
        return results[0]

    return None


def extract_search_results(raw_html):
    """Returns the search results.

    :param raw_html: Dump from any page.

    """
    results = re_search_result.findall(raw_html)

    return [(int(r[0]), r[1]) for r in results]
