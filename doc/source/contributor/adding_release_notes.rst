.. _adding_release_notes:

Release Notes
=============

What are release notes?
~~~~~~~~~~~~~~~~~~~~~~~

Release notes are important for change management within manila. Since manila
follows a release cycle with milestones, release notes provide a way for the
community and users to quickly grasp what changes occurred within a development
milestone. To the OpenStack release management and documentation teams,
release notes are a way to compile changes per milestone. These notes are
published on the `OpenStack Releases website <http://releases.openstack.org>`_.
Automated tooling is built around ``releasenotes`` and they get appropriately
handled per release milestone, including any back-ports to stable releases.

What needs a release note?
~~~~~~~~~~~~~~~~~~~~~~~~~~

* Changes that impact an upgrade, most importantly, those that require a
  deployer to take some action while upgrading

* A new feature is implemented
* An existing feature is deprecated
* An existing feature is removed
* Behavior of an existing feature has changed in a discernible way to an end
  user or administrator
* A security bug is fixed
* New configuration option is added

What does not need a release note?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* A code change that doesn't change the general behavior of any
  feature such as code refactor or logging changes. One case of this could be
  the removal of the python 2.x compatibility layer, i.e., the "six" library
  from code.
* Functional or unit test coverage enhancement
* Any change submitted with a justified TrivialFix flag added in the commit
  message
* Adding or changing documentation within in-tree documentation guides

How do I add a release note?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We use `Reno <https://docs.openstack.org/reno/latest/>`_ to create and manage
release notes. The new subcommand combines a random suffix with a "slug" value
to make the new file with a unique name that is easy to identify again later.
To create a release note for your change, use:

.. code-block:: console

    $ reno new slug-goes-here

If reno is not installed globally on your system, you can use a tox
environment in manila:

.. code-block:: console

    $ tox -e newnote -- slug-goes-here

.. note::

    When you are adding a bug-fix reno, name your file using the template:
    "bug-<launchpad-bug-id>-slug-goes-here".

Then add the notes in ``yaml`` format in the file created. Pay attention to the
type of section. The following are general sections to use:

prelude

  General comments about the change. The prelude from all notes in a
  release are combined, in note order, to produce a single prelude
  introducing the release.

features

  New features introduced

issues

  A list of known issues with respect to the change being introduced. For
  example, if the new feature in the change is experimental or known to not
  work in some cases, it should be mentioned here.

upgrade

  A list of upgrade notes in the release. Any removals that affect upgrades are
  to be noted here.

deprecations

  Any features, APIs, configuration options that the change has deprecated.
  Deprecations are not removals. Deprecations suggest that there will be
  support for a certain timeline. Deprecation should allow time for users
  to make necessary changes for the removal to happen in a future release.
  It is important to note the timeline of deprecation in this section.

critical

  A list of *fixed* critical bugs (descriptions only).

security

  A list of *fixed* security issues (descriptions only).

fixes

  A list of other *fixed* bugs (descriptions only).

other

  Other notes that are important but do not fall into any of the given
  categories.

::

   ---
   prelude: >
       Replace this text with content to appear at the
       top of the section for this change.
   features:
     - List new features here, or remove this section.
   issues:
     - List known issues here, or remove this section.
   upgrade:
     - List upgrade notes here, or remove this section.
   deprecations:
     - List deprecation notes here, or remove this section
   critical:
     - Add critical notes here, or remove this section.
   security:
     - Add security notes here, or remove this section.
   fixes:
     - Add normal bug fixes here, or remove this section.
   other:
     - Add other notes here, or remove this section.


Dos and Don'ts
~~~~~~~~~~~~~~
* Release notes need to be succinct. Short and unambiguous descriptions are
  preferred
* Write in past tense, unless you are writing an imperative statement
* Do not have blank sections in the file
* Do not include code or links
* Avoid special rst formatting unless absolutely necessary
* Always prefer including a release note in the same patch
* Release notes are not a replacement for developer/user/admin documentation
* Release notes are not a way of conveying behavior of any features or usage of
  any APIs
* Limit a release note to fewer than 2-3 lines per change per section
* OpenStack prefers atomic changes. So remember that your change may need the
  fewest sections possible
* General writing guidelines can be found
  `here <https://docs.openstack
  .org/doc-contrib-guide/writing-style/general-writing-guidelines.html>`_
* Proofread your note. Pretend you are a user or a deployer who is reading
  the note after a milestone or a release has been cut
