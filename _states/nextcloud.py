"""
Nextcloud Desktop salt state module
===================================

Manage Nextcloud Desktop user accounts, their authentication
and general options in nextcloud.cfg.
"""

import logging

import salt.exceptions
import salt.utils.dictdiffer

# import salt.utils.platform

log = logging.getLogger(__name__)

__virtualname__ = "nextcloud"


def __virtual__():
    return __virtualname__


def account_present(name, url, authtype="webflow", user=None):
    """
    Make sure an account is present in the local user's Nextcloud Desktop client config.

    name
        The local user's Nextcloud account name.

    url
        The server URL, including protocol prefix. No trailing dashes.

    authtype
        As seen in nextcloud.cfg, is usually 'webflow'. 'http' is valid also.
        Defaults to 'webflow'.

    user
        The local user to ensure the account presence for. Defaults to salt user.

    """
    ret = {"name": name, "result": True, "comment": "", "changes": {}}

    try:
        if __salt__["nextcloud.account_exists"](name, url, user):
            ret["comment"] = "Account is already present."
        elif __opts__["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "Account '{}' on '{}' would have been added for user '{}'.".format(
                name, url, user
            )
            ret["changes"] = {"added": name}
        elif __salt__["nextcloud.add_account"](name, url, authtype, user):
            ret["comment"] = "Account '{}' on '{}' was added for user '{}'.".format(
                name, url, user
            )
            ret["changes"] = {"added": name}
        else:
            ret["result"] = False
            ret["comment"] = "Something went wrong while calling nextcloud."
    except salt.exceptions.CommandExecutionError as e:
        ret["result"] = False
        ret["comment"] = str(e)

    return ret


def account_absent(name, url=None, user=None):
    """
    Make sure an account is absent from the local user's Nextcloud Desktop client config.
    This should be called after deauthenticating to not leave open sessions and
    unused keyring entries behind.

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    user
        The local user to ensure the account absence for. Defaults to salt user.

    """
    ret = {"name": name, "result": True, "comment": "", "changes": {}}

    try:
        if not __salt__["nextcloud.account_exists"](name, url, user):
            ret["comment"] = "Account is already absent."
        elif __opts__["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "Account '{}' on '{}' would have been removed for user '{}'.".format(
                name, url, user
            )
            ret["changes"] = {"removed": name}
        elif __salt__["nextcloud.remove_account"](name, url, user):
            ret["comment"] = "Account '{}' on '{}' was removed for user '{}'.".format(
                name, url, user
            )
            ret["changes"] = {"removed": name}
        else:
            ret["result"] = False
            ret["comment"] = "Something went wrong while calling nextcloud."
    except salt.exceptions.CommandExecutionError as e:
        ret["result"] = False
        ret["comment"] = str(e)

    return ret


def account_authenticated(
    name, url=None, password=None, password_pillar=None, keyring=None, user=None
):
    """
    Make sure an account present in the local user's Nextcloud Desktop client config
    is authenticated persistently using the system's default keyring. This currently
    works on MacOS only.

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    password
        The user's password for this account. Not recommended on CLI usage.
        password_pillar is generally preferred.

    password_pillar
        Pillar that contains the user's password for this account.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~user/Library/Keychains/login.keychain-db (MacOS).

    user
        The local user to ensure the account authentication for. Defaults to salt user.

    """
    ret = {"name": name, "result": True, "comment": "", "changes": {}}

    try:
        has_app_password = __salt__["nextcloud.has_app_password"](
            name, url, keyring, user
        )
        # for authentication, require the account be present in the config file
        if not __salt__["nextcloud.account_exists"](name, url, user):
            ret["result"] = False
            ret[
                "comment"
            ] = "Account {} on {} is not present in nextcloud.cfg for user {}. Make sure to call nextcloud.account_present first.".format(
                name, url, user
            )
            if has_app_password:
                ret[
                    "comment"
                ] += " It seems there is a keyring entry though. Delete it to avoid bugs."
            if __opts__["test"]:
                ret["result"] = None
                ret["comment"] += " Since this is a test run, this might be expected."
        if has_app_password:
            ret[
                "comment"
            ] = "Account {} on {} seems to be authenticated for user {}. If not, delete the keyring entry and try again.".format(
                name, url, user
            )
            return ret
            # @TODO supply force flag to renew auth

        # checking authentication does not work without external consequences, assume it works
        elif __opts__["test"]:
            ret["result"] = None
            ret[
                "comment"
            ] = "Account '{}' on '{}' would have been authenticated for user '{}'.".format(
                name, url, user
            )
            ret["changes"] = {"authenticated": name}
        # try to acquire an application password
        # elif (app_password := __salt__["nextcloud.authenticate"](name, url, password, password_pillar, user)):
        else:
            app_password = __salt__["nextcloud.authenticate"](
                name, url, password, password_pillar, user
            )
            if app_password:
                ret[
                    "comment"
                ] = "Account '{}' on '{}' was authenticated for user '{}'.".format(
                    name, url, user
                )
                ret["changes"] = {"authenticated": name}
            else:
                ret["result"] = False
                ret["comment"] = "Something went wrong while calling nextcloud."
                return ret
        # assume the password can be saved into the keyring because actually
        # testing without external consequences is too cumbersome
        if __opts__["test"]:
            ret[
                "comment"
            ] += " The application password would have been persisted in the system keychain."
        # persist the application password
        elif app_password and __salt__["nextcloud.save_app_password"](
            name, url, app_password, keyring, user
        ):
            ret["result"] = True
            ret[
                "comment"
            ] += " The application password has been persisted in the system keychain"
        else:
            ret["result"] = False
            ret[
                "comment"
            ] += " Something went wrong while trying to persist the authentication though."
    except salt.exceptions.CommandExecutionError as e:
        ret["result"] = False
        ret["comment"] = str(e)

    return ret


def account_deauthenticated(
    name, url=None, app_password=None, keyring=None, prompt=True, user=None
):
    """
    Make sure an account is deauthenticated persistently, ie the server session
    is closed and/or the password is absent from the system's default keyring.
    If you specify the url parameter, the account does not have to be present
    in the user's Nextcloud Desktop client config file.
    This currently works on MacOS only.
    To close session on server: specify app_password or set prompt=True. The
    application password will always be deleted, if present.

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    app_password
        Account password associated specifically with the local login session.
        It can be found in the keyring. Needed when promp=False and closing the
        server session is wanted.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS).

    prompt:
        Allow lookup of app_password in keyring by salt. On MacOS, the user will
        be prompted for permission (ie the process is interactive). Currently
        supported on MacOS only. Defaults to True.

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """
    ret = {"name": name, "result": True, "comment": "", "changes": {}}

    try:
        # if url was not specified and the account does not exist, we cannot
        # possibly autodiscover it. if it was not specified, the following
        # messages will be a bit borked though (None for url) since the actual
        # discovery is done in the execution module @FIXME
        if not url and not __salt__["nextcloud.account_exists"](name, user=user):
            ret["result"] = False
            ret[
                "comment"
            ] = "Account {} is not present in nextcloud.cfg for user {}. Make sure to call nextcloud.account_present first or specify url.".format(
                name, user
            )
            return ret

        has_app_password = __salt__["nextcloud.has_app_password"](
            name, url, keyring, user
        )

        if prompt and app_password is None:
            if not has_app_password:
                ret["result"] = False
                ret[
                    "comment"
                ] = "Could not autodiscover application password for account {} on {} for user {}. Set prompt=False to skip.".format(
                    name, url, user
                )
                return ret
            app_password = __salt__["nextcloud.get_app_password"](
                name, url, keyring, user
            )

        if app_password:
            if __opts__["test"]:
                ret["result"] = None
                ret[
                    "comment"
                ] = "Would have tried to deauthenticate account {} from the server at {} for user {}.".format(
                    name, url, user
                )
                ret["changes"]["session_closed"] = name
            elif __salt__["nextcloud.deauthenticate"](
                name, url, app_password, keyring, prompt, user
            ):
                ret[
                    "comment"
                ] = "Deauthenticated account {} from the server at {} for user {}.".format(
                    name, url, user
                )
                ret["changes"]["session_closed"] = name
            else:
                ret["result"] = False
                ret["comment"] = "Something went wrong while calling nextcloud."
                return ret

        if has_app_password:
            if __opts__["test"]:
                ret[
                    "comment"
                ] += " Would have deleted application password from keyring for account {} on server {} for user {}".format(
                    name, url, user
                )
                ret["changes"]["deleted"] = name
            elif __salt__["nextcloud.remove_app_password"](name, url, keyring, user):
                ret[
                    "comment"
                ] = " Deleted application password from keyring for account {} on server {} for user {}.".format(
                    name, url, user
                )
                ret["changes"]["deleted"] = name
                ret["result"] = True
            else:
                ret["result"] = False
                ret["comment"] = "Something went wrong while calling nextcloud."

    except salt.exceptions.CommandExecutionError as e:
        ret["result"] = False
        ret["comment"] = str(e)

    return ret


def options(options, sync=False, sync_accounts=False, user=None, name=None):
    """
    Make sure the local user's Nextcloud Desktop client configuration options
    are set as specified.

    options
        2-dimensional dictionary of options to set in nextcloud.cfg.
        First dimension defines sections, second one options.

    sync
        Sync option dict to file instead of only updating. Does not apply to Accounts section.
        Defaults to False.

    sync_accounts
        Sync option dict to file, including Accounts section. Defaults to False.

    user
        The local user to ensure the account presence for. Defaults to salt user.

    name
        exists for technical reasons since salt expects a state to accept it

    """
    ret = {"name": name, "result": True, "comment": "", "changes": {}}

    # activating account sync syncs the rest as well
    sync = sync or sync_accounts

    try:
        changed, changes = _compare_options(options, sync, sync_accounts, user)

        if not changed:
            ret["comment"] = "Options are already set as specified for user {}.".format(
                user
            )

        elif __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Options would have been {} for user '{}'.".format(
                "synced" if sync else "updated", user
            )
            ret["changes"] = changes

        elif sync and __salt__["nextcloud.set_options"](options, sync_accounts, user):
            ret["comment"] = "Options have been synced for user '{}'.".format(user)
            if sync_accounts:
                ret["comment"] += " Accounts have been synced as well."
            ret["changes"] = changes

        elif __salt__["nextcloud.update_options"](options, user):
            ret["comment"] = "Options have been updated for user '{}'.".format(user)
            ret["changes"] = changes
        else:
            ret["result"] = False
            ret["comment"] = "Something went wrong while calling nextcloud."
    except salt.exceptions.CommandExecutionError as e:
        ret["result"] = False
        ret["comment"] = str(e)

    return ret


def _compare_options(options, sync, sync_accounts, user):
    current = __salt__["nextcloud.get_options"](user)
    log.debug("Current options:\n\n{}".format(current))
    log.debug("Requested options:\n\n{}".format(options))
    changes = {}
    cumulative = []

    # tell dictdiffer to include newly missing keys if sync is requested
    diff = PatchedRecursiveDiffer(current, options, ignore_missing_keys=not sync)
    changed = diff.changed()
    added = diff.added()
    removed = diff.removed()

    cumulative += added
    cumulative += changed

    # dictdiffer returns a list of changed keys in parent.child notation
    if not sync_accounts:
        removed = [x for x in removed if "Accounts" != x[:8]]
    if sync:
        cumulative += removed

    changes["added"] = added
    changes["changed"] = changed
    changes["removed"] = removed
    return bool(cumulative), changes


class PatchedRecursiveDiffer(salt.utils.dictdiffer.RecursiveDictDiffer):
    def added(self, include_nested=False):
        """
        Returns all keys that have been added.

        include_nested
            If an added key contains a dictionary, include its
            keys in dot notation as well. Defaults to false.

        If the keys are in child dictionaries they will be represented with
        . notation.

        This works for added nested dicts as well, where the parent class
        tries to access keys on non-dictionary values and throws an exception.
        """
        return sorted(self._it("old", "new", include_nested))

    def removed(self, include_nested=False):
        """
        Returns all keys that have been removed.

        include_nested
            If an added key contains a dictionary, include its
            keys in dot notation as well. Defaults to false.

        If the keys are in child dictionaries they will be represented with
        . notation

        This works for removed nested dicts as well, where the parent class
        tries to access keys on non-dictionary values and throws an exception.
        """
        return sorted(self._it("new", "old", include_nested))

    def _it(
        self, key_a, key_b, include_nested=False, diffs=None, prefix="", is_nested=False
    ):
        keys = []
        if diffs is None:
            diffs = self.diffs

        for key in diffs.keys():
            if is_nested:
                keys.append("{}{}".format(prefix, key))

            if not isinstance(diffs[key], dict):
                continue

            if is_nested:
                keys.extend(
                    self._it(
                        key_a,
                        key_b,
                        diffs=diffs[key],
                        prefix="{}{}.".format(prefix, key),
                        is_nested=is_nested,
                        include_nested=include_nested,
                    )
                )
            elif "old" not in diffs[key]:
                keys.extend(
                    self._it(
                        key_a,
                        key_b,
                        diffs=diffs[key],
                        prefix="{}{}.".format(prefix, key),
                        is_nested=is_nested,
                        include_nested=include_nested,
                    )
                )
            elif diffs[key][key_a] == self.NONE_VALUE:
                keys.append("{}{}".format(prefix, key))

                if isinstance(diffs[key][key_b], dict) and include_nested:
                    keys.extend(
                        self._it(
                            key_a,
                            key_b,
                            diffs=diffs[key][key_b],
                            is_nested=True,
                            prefix="{}{}.".format(prefix, key),
                            include_nested=include_nested,
                        )
                    )
        return keys
