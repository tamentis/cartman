cartman
=======

*cartman* is an overweight, immature, spoiled, outspoken, lazy, foul-mouthed,
mean-spirited, racist, sexist, anti-semitic, xenophobic, sociopathic,
narcissistic, and ill-tempered elementary school student living with his
mother. Wait... wrong cartman.

*cartman* allows you to create and manage your Trac_ tickets from the
command-line, without the need to setup physical access to the Trac_
installation/database. All you need is a Trac_ account.

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

Configuration Options
^^^^^^^^^^^^^^^^^^^^^

Required Settings:

 - base_url
 - username
 - password

Optional Settings:

 - auth_type
 - verify_ssl_cert

The ``auth_type`` will force cartman to use the give authtication type.
Currently supported auth values are: basic, digest. If not specified defaults
to basic (which is the most unsafe option).

The ``verify_ssl_cert`` will force cartman to access an SSL site with a
self-signed or invalid SSL certificate. Use this with care.


Command walk through
--------------------

Report Listing
^^^^^^^^^^^^^^

Dump a list of tickets on screen, without details::

    $ cm report 1
    #142. fix world hunger (bjanin@)
    #159. ignore unpaid rent (bjanin@)

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


Hacking
-------
 - Create a temp Trac for testing purpose (in virtualenv)::

    $ pip install trac
    $ trac-admin testtrac initenv
    $ htpasswd -b -c -m htpasswd testuser testpass
    $ tracd testtrac -p 8080 --basic-auth=.,htpasswd,testrealm

TODO
----
 - find a way to read comments (tricky because there is nothing that dumps the
   comments in their raw format in the default Trac installation).
 - create a few shortcuts:
   - cm fixed 1
   - cm accept 1
   - cm invalid 1
 - improve editor handling to allow better test units
 - add query support, allowing them to be defined in the config file.
 - add curses support to navigate tickets easily.
 - store the cookie somewhere to avoid pulling it all the time and waste time
   in index/login.
 - write a cartman daemon that will poll a mailbox for new emails and create
   tickets from them and later allow to reply to comments, attach files, etc.


.. _Trac: http://trac.edgewall.org/
.. _vim: http://www.vim.org/
.. _mutt: http://www.mutt.org/
