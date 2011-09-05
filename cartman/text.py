"""
Various text processing functions.
"""

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
    except ValueError:
        raise exceptions.InvalidParameter(
                "invalid identifier (should be an int)")

    return converted_id

