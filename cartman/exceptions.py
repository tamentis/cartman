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


class CartmanException(Exception):
    """Define the prefix to use on error messages."""
    prefix = "error"


class UsageException(CartmanException):
    """Base class for any program usage errors/exceptions."""


class InvalidParameter(UsageException):
    """A parameter for the command is invalids (wrong type?)."""


class FatalError(CartmanException):
    """Unrecoverable error during runtime."""


class ConfigError(FatalError):
    """Configuration file is not usable."""
    prefix = "config"


class UnknownCommand(FatalError):
    """Command is not defined."""


class RequestException(FatalError):
    """A request to Trac failed."""


class LoginError(RequestException):
    """Raise when unable to login."""
