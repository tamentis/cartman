cartman
=======

*cartman* allows you to create and manage your Trac_ tickets from the
command-line, without the need to setup physical access to the Trac_
installation/database or even the need to install a plugin on Trac_.  All you
need is a Trac_ account.

Examples
--------
Create a new ticket, that will open your $EDITOR::

    $ cm new

View the content of a ticket::

    $ cm view 1514

Configuration
-------------
At a minimum you need to create a ``~/.cartman/config`` file with the
following::

    [trac]
    base_url = http://your.trac.install/
    username = tamentis
    password = sitnemat

The password can also be specified through a `TRAC_PASSWORD`
environment variable, which overrides the above `password` field.

Configuration Options
^^^^^^^^^^^^^^^^^^^^^
Each section represent a site which can be selected using the ``-s``
command-line argument.  Within each section, the following settings are
available:

- ``base_url`` - required, defines the URL of your Trac system
- ``auth_type`` - forces an authentication type, currently available: ``basic``
  (default), ``digest``, ``acctmgr`` or ``none``.
- ``username`` - required if ``auth_type`` is not ``none``
- ``password`` - required if ``auth_type`` is not ``none``
- ``verify_ssl_cert`` - ignore self-signed or invalid SSL certificates if set
  to false.
- ``editor`` - override the editor defined the ``$EDITOR`` environment
  variable.


Command walk through
--------------------

Report Listing and Search
^^^^^^^^^^^^^^^^^^^^^^^^^
Dump a list of tickets on screen, without details::

    $ cm report 1
    #142. fix world hunger (bjanin@)
    #159. ignore unpaid rent (bjanin@)

Another way to find ticket is using the search command::

    $ cm search dead mouse
    #154. mickey

Ticket View
^^^^^^^^^^^
Show all the properties of a ticket::

    $ cm view 1

List of Reports
^^^^^^^^^^^^^^^
Get a list of all the available reports with::

    $ cm reports

System Properties
^^^^^^^^^^^^^^^^^
This will dump on screen all the Milestones, Components, Versions::

    $ cm properties

Creating a ticket
^^^^^^^^^^^^^^^^^
Creating a ticket will work similarly to writing a new email in mutt_, it loads
your current ``$EDITOR`` and lets you edit the details of the ticket. Assuming
all the parameters are correct, it will create the ticket as soon as you save
and exit and return the ticket number. If your ticket does not appear valid
(missing required field, inexistent Milestone, etc.) *cartman* will stop and
lists each error and let you return to your editor::

    $ cm new
    -- opens your editor --

    Found the following errors:
     - Invalid 'Subject': cannot be blank
     - Invalid 'Milestone': expected: Bug Bucket, Release 2, Release 3

    -- Hit Enter to return to editor, ^C to abort --

The first parameter to ``cm`` is the owner of the ticket, it populates the
``To`` field by default::

    $ cm new jcarmack

If your Trac has custom fields, you can use their identifier in the headers,
e.g.::

    story_id: 5123
    iteration: 15

If you specify a template with -t, cartman will look for a matching file in the
``~/.cartman/templates`` folder and will use it as a base for your ticket::

    $ cm new -t sysadmin

You can define a ``default`` template in this same directory in order to set
the template used by default (without ``-t``).

Commenting on a ticket
^^^^^^^^^^^^^^^^^^^^^^
Just like creating a ticket, adding a comment is just like mutt_, your current
``$EDITOR`` will be loaded on a blank file for you to edit. Upon save and exit,
*cartman* will commit this new comment and return silently, unless an error
occurs::

    $ cm comment 1

If the comment is short enough to fit on the command line, you may use the
``-m`` flag as such::

    $ cm comment 1 -m "you forgot to call twiddle()"

View/Set the status of a ticket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
View the current status of a ticket, and the available statuses::

    $ cm status 1

Set a ticket as accepted::

    $ cm status 1 accept

If you need to add a comment with this status change, you can use the ``-c``
flag, it will open your default editor::

    $ cm status 1 reopen -c

You may also use the ``-m`` flag to define the comment in-line, without the use
of an editor::

    $ cm status 1 reopen -m "does not work with x = y"

Advanced configuration
----------------------
If you are using vim_ as your default editor, you also might want to add
email-like syntax highlighting to match the ``.cm.ticket`` extension::

    autocmd BufNewFile *.cm.ticket setf mail

If you use multiple Trac sites, you can have multiple configurations in the
same file using the section to separate the sites, here is an example::

    [other]
    base_url = http://other.trac.site/
    username = tamentis
    password = sitnemat
    verify_ssl_cert = False


You would pass the ``-s`` parameter to ``cm`` to define which site to access::

    cm -s other report 1

You may define all common configuration settings in the ``[DEFAULT]`` section.

Using cartman without editor
----------------------------
You may need to integrate cartman with other software where opening an editor
does not make sense.  In that case you can automatically create tickets from
a file using the ``--message-file`` option::

    cm new --message-file=secerror.txt

This file would need to contain a complete ticket, if anything is missing,
cartman will exit with an error message.

Installation
------------
Quick and dirty if you are not familiar with Python packaging::

    sudo python setup.py install

Requirements
------------
- Python 2.7+, 3.3+ (not 3.2, not 2.6)
- python-requests 1.2 and above


Compatibility
-------------
- Tested on Trac 0.12.5 and 1.2.x
- Probably still works on 0.11, but untested.


Hacking
-------
- The following command will create one virtualenv and sandbox for each latest
  0.12, 1.0 and 1.2 releases of Trac::

    $ ./tools/mkenv.sh

- You can then serve one or the other using, the default admin user/pass is
  sandbox/sandbox::

    $ ./tools/serve-0.12.sh
    $ ./tools/serve-1.0.sh
    $ ./tools/serve-1.2.sh

- Follow PEP-8, existing style then the following notes.
- For dictionaries, lists: keep commas after each items, closing bracket
  should close on the same column as the first letter of the statement with the
  opening bracket.
- Use double-quotes for strings unless it makes it easier on certain strings
  (avoids escaped double-quotes).
- If an error is exceptional, let the exception rise.


Distribute
----------
- Change the version in cartman/__init__.py, update CHANGES.txt
- Commit
- Create a tag::

    git tag -a vX.Y.Z -m 'Releasing vX.Y.Z'
    git push --tags

- Download the file from github (release section),
- Sign it::

    gpg --armor --detach-sig cartman-X.Y.Z.tar.gz

- Distribute on Pypi::

    python setup.py sdist upload


.. _Trac: http://trac.edgewall.org/
.. _vim: http://www.vim.org/
.. _mutt: http://www.mutt.org/
