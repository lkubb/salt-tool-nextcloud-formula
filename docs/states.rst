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



