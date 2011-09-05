"""
Various text processing functions.
"""

import re
import json
import difflib

import exceptions


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

    matches = difflib.get_close_matches(value, options.keys())

    if not matches:
        for l_opt, opt in options.items():
            pattern = r".*\b%s\b.*" % value
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

def extract_timestamp(raw_html):
    """Given a dump of HTML data, extract the timestamp and return it as a
    string value.

    :param raw_html: Dump from the ticket page.

    """
    m = re.search(r"""name="ts" value="([^"]+)""", raw_html, re.MULTILINE)
    if m:
        timestamp = m.group(1)
    else:
        raise exceptions.FatalError("unable to fetch timestamp")

    return timestamp

def extract_statuses(raw_html):
    """Given a dump of HTML data, extract the timestamp and return it as a
    string value.

    :param raw_html: Dump from the ticket page.

    """
    re_status = r'<input type="radio" [^<]+ name="action" value="([^"]+)'
    return re.findall(re_status, raw_html)

def extract_properties(raw_html):
    """Return all the values typically used in drop-downs on the create
    ticket page, such as Milestones, Versions, etc. These lists are
    extracted from the JavaScript dictionary exposed on the query page.

    """
    re_prop = r"var properties=([^;]+)"
    prop_tokens = re.findall(re_prop, raw_html, re.MULTILINE)

    if len(prop_tokens) < 1:
        return {}

    return json.loads(prop_tokens[0])

