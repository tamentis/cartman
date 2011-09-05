"""
Helper functions for console display interface.
"""

def underline(text):
    """Given a string, return a series of dash with the same length.

    :param text: Text used as reference to create a line of len(text)
                    dashes.
    """
    return "-" * len(text)


def title(text):
    """Returns the same string with a line of dashes of the same size.

    :param text: Text to return underlined.
    """
    if not text:
        return ""

    return text + "\n" + underline(text)

