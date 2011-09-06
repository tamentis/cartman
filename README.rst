cartman
=======

*cartman* is an overweight, immature, spoiled, outspoken, lazy, foul-mouthed,
mean-spirited, racist, sexist, anti-semitic, xenophobic, sociopathic,
narcissistic, and ill-tempered elementary school student living with his
mother. Wait... wrong cartman.

*cartman* allows you to create and manage your Trac_ tickets from the
command-line, without the need to setup physical access to the Trac_
installation/database. All you need is a Trac_ account.

Configuration
-------------
At a minimum you need to create a ``~/.cartmanrc`` file with the following::

    [trac]
    base_url = http://your.trac.install/
    username = tamentis
    password = sitnemat

If you are using vim_ as your default editor, you also might want to add
email-like syntax highlighting to match the ``.cm.ticket`` extension::

    autocmd BufNewFile *.cm.ticket setf mail

Walkthrough
-----------

Report Listing
^^^^^^^^^^^^^^

Dump a list of tickets on screen, without details::

    $ cm report 1
    #142. fix world hunger (bjanin@)
    #159. ignore unpaid rent (bjanin@)

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

Setting the status of a ticket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set a ticket as accepted::

    $ cm status 1 accept

If you need to add a comment with this status change, you can use the ``-c``
flag, it will open your default editor::

    $ cm status 1 reopen -c

You may also use the ``-m`` flag to define the comment inline, without the use
of an editor::

    $ cm status 1 reopen -m "does not work with x = y"

TODO
----
 - find a way to read comments (tricky because there is nothing that dumps the
   comments in their raw format in the default Trac installation).
 - view status (and available ones for the given ticket)
 - pull the report name for the ``report`` command.
 - create a few shortcuts:
   - cm fixed 1
   - cm accept 1
   - cm invalid 1
 - improve editor handling to allow better test units
 - sort tickets by id on ``report``.
 - add query support, allowing them to be defined in the config file.
 - add multi configuration with [DEFAULT] (to have multiple sites).


.. _Trac: http://trac.edgewall.org/
.. _vim: http://www.vim.org/
.. _mutt: http://www.mutt.org/
