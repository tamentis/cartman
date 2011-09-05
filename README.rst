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

TODO
----
 - find a way to read comments
 - set/view status (with optional comment)
 - pull the report name for the ``report`` command.


.. _Trac: http://trac.edgewall.org/
.. _vim: http://www.vim.org/
.. _mutt: http://www.mutt.org/
