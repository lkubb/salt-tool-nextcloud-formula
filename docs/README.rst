.. _readme:

Nextcloud Desktop Formula
=========================

Manages Nextcloud Desktop client in the user environment, including user accounts and authentication (the latter for MacOS only currently)..

.. contents:: **Table of Contents**
   :depth: 1

Usage
-----
Applying ``tool_nextcloud`` will make sure ``nextcloud`` is configured as specified.

Authentication setup
~~~~~~~~~~~~~~~~~~~~
You can configure this formula to automatically login user accounts as well. This currently works on MacOS only. Accounts that are configured this way will prompt the user for Keychain Access authentication when Nextcloud starts. Click ``Allow always`` to silence that prompt.

Execution and state module
~~~~~~~~~~~~~~~~~~~~~~~~~~
This formula provides a relatively large custom execution module and state to manage user accounts, their authentication and general Nextcloud options in ``nextcloud.cfg``. The functions are self-explanatory, please see the source code or the rendered docs at :ref:`em_nextcloud` and :ref:`sm_nextcloud`.

Configuration
-------------

This formula
~~~~~~~~~~~~
The general configuration structure is in line with all other formulae from the `tool` suite, for details see :ref:`toolsuite`. An example pillar is provided, see :ref:`pillar.example`. Note that you do not need to specify everything by pillar. Often, it's much easier and less resource-heavy to use the ``parameters/<grain>/<value>.yaml`` files for non-sensitive settings. The underlying logic is explained in :ref:`map.jinja`.

User-specific
^^^^^^^^^^^^^
The following shows an example of ``tool_nextcloud`` per-user configuration. If provided by pillar, namespace it to ``tool_global:users`` and/or ``tool_nextcloud:users``. For the ``parameters`` YAML file variant, it needs to be nested under a ``values`` parent key. The YAML files are expected to be found in

1. ``salt://tool_nextcloud/parameters/<grain>/<value>.yaml`` or
2. ``salt://tool_global/parameters/<grain>/<value>.yaml``.

.. code-block:: yaml

  user:

      # Force the usage of XDG directories for this user.
    xdg: true

      # Persist environment variables used by this formula for this
      # user to this file (will be appended to a file relative to $HOME)
    persistenv: '.config/zsh/zshenv'

      # Add runcom hooks specific to this formula to this file
      # for this user (will be appended to a file relative to $HOME)
    rchook: '.config/zsh/zshrc'

      # This user's configuration for this formula. Will be overridden by
      # user-specific configuration in `tool_nextcloud:users`.
      # Set this to `false` to disable configuration for this user.
    nextcloud:
        # You can specify accounts as well. If password[_pillar] is set, Salt
        # will try to authenticate them automatically and save to the system keyring.
        # Currently only supported on MacOS.
      accounts:
        - name: nextcloud-common-user
            # better use password_pillar instead
          password: mediocre_nextcloud-password...
            # avoids disk writes (state cache)
          password_pillar: tool:nextcloud:password
          url: https://cloud.test.com
        # These are configuration options in nextcloud.cfg. `Section: {option: value}`
      config:
        General:
            # Booleans need to be lowercase strings!
          optionalServerNotifications: 'false'
        # Delete all other options not specified in config for this user.
      sync_config: false

Formula-specific
^^^^^^^^^^^^^^^^

.. code-block:: yaml

  tool_nextcloud:

      # Default formula configuration for all users.
    defaults:
      config: default value for all users

Config file serialization
~~~~~~~~~~~~~~~~~~~~~~~~~
This formula serializes configuration into a config file. A default one is provided with the formula, but can be overridden via the TOFS pattern. See :ref:`tofs_pattern` for details.


Available states
----------------

The following states are found in this formula:

.. contents::
   :local:


``tool_nextcloud``
~~~~~~~~~~~~~~~~~~
*Meta-state*.

Performs all operations described in this formula according to the specified configuration.


``tool_nextcloud.package``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Installs the Nextcloud Desktop package only.


``tool_nextcloud.config``
~~~~~~~~~~~~~~~~~~~~~~~~~
Manages the Nextcloud Desktop package configuration by

* managing/serializing the config file

Has a dependency on `tool_nextcloud.package`_.


``tool_nextcloud.accounts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~



``tool_nextcloud.clean``
~~~~~~~~~~~~~~~~~~~~~~~~
*Meta-state*.

Undoes everything performed in the ``tool_nextcloud`` meta-state
in reverse order.


``tool_nextcloud.package.clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Removes the Nextcloud Desktop package.
Has a dependency on `tool_nextcloud.config.clean`_.


``tool_nextcloud.config.clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Removes the configuration of the Nextcloud Desktop package.


``tool_nextcloud.accounts.clean``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




Development
-----------

Contributing to this repo
~~~~~~~~~~~~~~~~~~~~~~~~~

Commit messages
^^^^^^^^^^^^^^^

Commit message formatting is significant.

Please see `How to contribute <https://github.com/saltstack-formulas/.github/blob/master/CONTRIBUTING.rst>`_ for more details.

pre-commit
^^^^^^^^^^

`pre-commit <https://pre-commit.com/>`_ is configured for this formula, which you may optionally use to ease the steps involved in submitting your changes.
First install  the ``pre-commit`` package manager using the appropriate `method <https://pre-commit.com/#installation>`_, then run ``bin/install-hooks`` and
now ``pre-commit`` will run automatically on each ``git commit``.

.. code-block:: console

  $ bin/install-hooks
  pre-commit installed at .git/hooks/pre-commit
  pre-commit installed at .git/hooks/commit-msg

State documentation
~~~~~~~~~~~~~~~~~~~
There is a script that semi-autodocuments available states: ``bin/slsdoc``.

If a ``.sls`` file begins with a Jinja comment, it will dump that into the docs. It can be configured differently depending on the formula. See the script source code for details currently.

This means if you feel a state should be documented, make sure to write a comment explaining it.

Todo
----
* default url
* folder sync setup::

    0\Folders\1\ignoreHiddenFiles=false
    0\Folders\1\journalPath=.sync_<12hashchars>.db
    0\Folders\1\localPath=/Users/user/Nextcloud/
    0\Folders\1\paused=false
    0\Folders\1\targetPath=/
    0\Folders\1\version=2
    0\Folders\1\virtualFilesMode=off
