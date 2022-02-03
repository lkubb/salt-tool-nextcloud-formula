"""
Nextcloud Desktop Salt Execution Module
Manage Nextcloud Desktop user accounts, their authentication
and general options in nextcloud.cfg.

======================================================

"""

from salt.exceptions import CommandExecutionError
import logging
import configparser
from xml.etree import ElementTree

import salt.utils.platform
import salt.utils.http

log = logging.getLogger(__name__)
__virtualname__ = "nextcloud"


def __virtual__():
    if salt.utils.platform.is_darwin() or \
       salt.utils.platform.is_linux() or \
       salt.utils.platform.is_windows():
        return __virtualname__

    raise CommandExecutionError("Platform not supported.")


def _where(user=None):
    if user is None:
        user = __salt__['environ.get']('USER')
        log.warn("Nextcloud was called without local user account specified. Defaulting to current salt user {}.".format(user))

    if salt.utils.platform.is_darwin():
        return __salt__['user.info'](user)['home'] + '/Library/Preferences/Nextcloud/nextcloud.cfg'
    elif salt.utils.platform.is_linux():
        return __salt__['cmd.run']("echo ${XDG_CONFIG_HOME:-$HOME/.config}/Nextcloud/nextcloud.cfg")
    elif salt.utils.platform.is_windows():
        return __salt__['user.info'](user)['home'] + '\\AppData\\Roaming\\Nextcloud\\nextcloud.cfg'

    raise CommandExecutionError("Platform not supported.")


def account_exists(name, url=None, user=None):
    """
    Check if specified account is present in user's Nextcloud Desktop client config.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.account_exists nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    user
        The local user to check the client config for. Defaults to salt user.

    """
    try:
        _get_account(name, url, user)
    except CommandExecutionError:
        return False
    return True


def add_account(name, url, authtype='webflow', user=None):
    """
    Add account to local user's Nextcloud Desktop client config.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.add_account nc-username https://cloud.test.com user=localuser

    name
        The local user's Nextcloud account name.

    url
        The server URL, including protocol prefix. No trailing dashes.

    authtype
        As seen in nextcloud.cfg, is usually 'webflow'. 'http' is valid also.
        Defaults to 'webflow'.

    user
        The local user to add the account for. Defaults to salt user.

    """
    if account_exists(name, url, user):
        raise CommandExecutionError("Account {} on {} already exists in nextcloud.cfg for user {}.".format(name, url, user))

    account = _serialize_account(name, url, authtype, user)
    c = _update_cfg("Accounts", account, user=user)
    return _save_cfg(c, user)


def remove_account(name, url=None, user=None):
    """
    Remove account from local user's Nextcloud Desktop client config.
    This should be called after deauthenticating to not leave open
    sessions and unused keyring entries behind.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.remove_account nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    user
        The local user to remove the account for. Defaults to salt user.

    """
    if not account_exists(name, url, user):
        raise CommandExecutionError("Account {} on {} does not exist in nextcloud.cfg for user {}.".format(name, url, user))

    _, i = _get_account(name, url, user)

    c = _get_parsed_cfg(user)
    for opt in c["Accounts"].keys():
        if '{}\\'.format(i) == opt[:2]:
            c.remove_option("Accounts", opt)
    if not _save_cfg(c, user):
        raise CommandExecutionError("Could not save nextcloud.cfg while removing account {} on {} for user {}.".format(name, url, user))

    return True


def authenticate(name, url=None, password=None, password_pillar=None, user=None):
    """
    Authenticate user to Nextcloud instance to retrieve an application password.
    Persisting this password automatically is currently possible on MacOS.
    There, on Nextcloud startup, the user will be asked if he wants to allow
    access to the new password entry (not sure why exactly, -T specifies ACL).

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.authenticate nc-username password_pillar=nc:pass user=localuser

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

    user
        The local user to authenticate the account for. Defaults to salt user.

    """
    if password is None and password_pillar:
        password = __salt__['pillar.get'](password_pillar)

    if password is None:
        raise CommandExecutionError("You need to specify either password or password_pillar for user {} on {}. It's also possible the password_pillar was not found".format(name, url))

    if url is None:
        url = _get_account(name, user=user)["url"]

    app_password = _authenticate_request(name, url, password, user)

    if app_password:
        return app_password
    raise CommandExecutionError("Something went wrong while requesting the application password for {} on {} for user {}".format(name, url, user))


def deauthenticate(name, url=None, app_password=None, prompt=False, keyring=None, user=None):
    """
    Deauthenticate user from Nextcloud instance. Mindthat the app_password
    is different from the user's password. It can be autodiscovered if the
    user gives permission during the interactive prompt.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.deauthenticate nc-username prompt=True user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes. If specified, execution does not need entry in cfg.

    app_password
        Account password associated specifically with the local login session.
        It can be found in the keyring. Needed when prompt=False.

    prompt
        Allow lookup of app_password in keyring by salt. On MacOS, the user will
        be prompted for permission (ie the process is interactive). Currently
        supported on MacOS only. Defaults to False.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS). Needed
        for autodiscovery of application password.

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """

    # online logout needs app password. can be read from keyring if user prompts are OK
    if not app_password or prompt:
        raise CommandExecutionError("Deauthentication needs application password or permission to prompt. Missing for account {} on {} for user {}".format(name, url, user))

    if url is None:
        url = _get_account(name, user=user)["url"]

    if prompt and app_password is None:
        app_password = get_app_password(name, url, keyring, user)

    if app_password:
        # don't care about the return value here. returns false on 404, so that might
        # mean the session was closed already @TODO consider the semantics here
        _deauthenticate_request(name, url, app_password, user)
        return True

    raise CommandExecutionError("Could not deauthenticate account {} from {} for user {}. Could not autodiscover app password.".format(name, url, user))


def update_options(options, user=None):
    """
    Set Nextcloud Desktop client configuration options as seen in nextcloud.cfg.
    It will not overwrite current configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.update_options '{General: {optionalServerNotifications: True}}' localuser

    options
        2-dimensional dictionary of options to set in nextcloud.cfg.
        First dimension defines sections, second one options.

    user
        The local user to change the client config for. Defaults to salt user.

    """

    c = _get_parsed_cfg(user)

    for section, opts in options.items():
        c = _update_cfg(section, opts, c, user)

    return _save_cfg(c, user)


def set_options(options, accounts=False, user=None):
    """
    Set Nextcloud Desktop client configuration options as seen in nextcloud.cfg.
    It **will overwrite** current configuration, except for Accounts section
    by default, where it will update.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.set_options '{General: {optionalServerNotifications: True}}' localuser

    options
        2-dimensional dictionary of options to set in nextcloud.cfg.
        First dimension defines sections, second one options.

    accounts
        Delete settings absent from options dict in Account section,
        instead of only updating specified ones. Defaults to False. Take care.

    user
        The local user to change the client config for. Defaults to salt user.

    """

    nc = configparser.ConfigParser()
    nc.optionxform = str  # case-sensitive read/write
    nc.read_dict(options)

    c = _get_parsed_cfg(user)

    if accounts or "Accounts" not in c.sections():
        return _save_cfg(nc, user)

    for opt, val in c["Accounts"].items():
        if not nc.has_option("Account", opt):
            nc["Accounts"][opt] = val
    return _save_cfg(nc, user)


def get_options(user=None):
    """
    Get Nextcloud Desktop client configuration options from nextcloud.cfg.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.get_options localuser

    user
        The local user to load the client config for. Defaults to salt user.

    """

    opts = {}

    c = _get_parsed_cfg(user)
    for section in c.sections():
        opts[section] = {}
        for opt, val in c[section].items():
            opts[section][opt] = val

    return opts


def get_app_password(name, url, keyring=None, user=None):
    """
    Get the **application** password for a local user's Nextcloud account.
    This will prompt for authentication on MacOS, where it is currently
    supported.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.get_app_password nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS).

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """
    if salt.utils.platform.is_darwin():
        app_password = _macos_get_authentication(name, url, keyring, user)
        # if not (app_password := _macos_get_authentication(name, url, keyring, user)):
        if not app_password:
            raise CommandExecutionError("Could not retrieve application password for {} on {} for user {}.".format(name, url, user))

    if app_password:
        return app_password

    raise CommandExecutionError("Keyring management is not supported for platform.")


def has_app_password(name, url, keyring=None, user=None):
    """
    Checks if the keyring contains the **application** password for a
    local user's Nextcloud account. This will prompt for authentication on
    MacOS, where it is currently supported. The account does not have to
    be present in the user's nextcloud.cfg, this just checks the keyring.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.has_app_password nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS).

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """
    if salt.utils.platform.is_darwin():
        if _macos_has_authentication(name, url, keyring, user):
            return True
    else:
        raise CommandExecutionError("Keyring management is not supported for platform.")

    return False


def remove_app_password(name, url, keyring=None, user=None):
    """
    Removes the **application** password for a local user's Nextcloud account
    from the system keyring. This will prompt for authentication on
    MacOS, where it is currently supported.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.has_app_password nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS).

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """
    if salt.utils.platform.is_darwin():
        if _macos_delete_authentication(name, url, keyring, user):
            return True
    else:
        raise CommandExecutionError("Keyring management is not supported for platform.")

    raise CommandExecutionError("Failed deleting application password for account {} on {} for user {}.".format(name, url, user))


def save_app_password(name, url, app_password, keyring=None, user=None):
    """
    Saves the **application** password for a local user's Nextcloud account
    to the system keyring. The account does not have to be present in the
    user's nextcloud.cfg. Currently supported for MacOS only.

    CLI Example:

    .. code-block:: bash

        salt '*' nextcloud.has_app_password nc-username user=localuser

    name
        The local user's Nextcloud account name.

    url
        If there is more than one account with the same name, makes it possible
        to filter by server URL as well. Specify including protocol prefix.
        No trailing dashes.

    app_password
        Account password associated specifically with the local login session.
        It can be found in the keyring. Needed when prompt=False.

    keyring
        Absolute path to the default keyring file. If not specified, it will
        be assumed to be ~/Library/Keychains/login.keychain-db (MacOS).

    user
        The local user to deauthenticate the account for. Defaults to salt user.

    """
    if salt.utils.platform.is_darwin():
        if _macos_save_authentication(name, app_password, url, keyring, user):
            return True
    else:
        raise CommandExecutionError("Keyring management is not supported for platform.")

    raise CommandExecutionError("Failed deleting application password for account {} on {} for user {}.".format(name, url, user))


def _authenticate_request(name, url, password, user=None):
    # User-Agent header is used as session name. MacOS is identified as Macintosh
    system = __grains__['kernel']
    if "Darwin" == system:
        system = "Macintosh"

    headers = {
        'User-Agent': '{} (Desktop Client - {})'.format(__grains__['host'], system),
        'OCS-APIRequest': 'true'
    }

    response = salt.utils.http.query(
        '{}/ocs/v2.php/core/getapppassword'.format(url),
        header_dict=headers,
        username=name,
        password=password,
        decode=True,
        decode_type="xml",
        status=True
    )

    # data = ElementTree.fromstring(response.content)

    if 200 != response['status']:
        raise CommandExecutionError("Nextcloud authentication failed with HTTP status code {}.".format(response["status"]))

    return response['dict'][1]['apppassword']


def _deauthenticate_request(name, url, app_password, user=None):
    # User-Agent header is used as session name. MacOS is identified as Macintosh
    system = __grains__['kernel']
    if "Darwin" == system:
        system = "Macintosh"

    headers = {
        'User-Agent': '{} (Desktop Client - {})'.format(__grains__['host'], system),
        'OCS-APIRequest': 'true'
    }

    response = salt.utils.http.query(
        '{}/ocs/v2.php/core/apppassword'.format(url),
        method='DELETE',
        header_dict=headers,
        username=name,
        password=app_password
    )

    data = ElementTree.fromstring(response.content)

    statuscode = data.findall('.//statuscode')[0].text

    # if '200' == (statuscode := data.findall('.//statuscode')[0].text):
    if '200' == statuscode:
        return True
    # assumption: app password was not found, therefore it was already absent
    elif '404' == statuscode:
        return False
    raise CommandExecutionError("Nextcloud deauthentication failed with HTTP status code {}.".format(statuscode))


def _macos_has_authentication(name, url, keychain=None, user=None):
    if keychain is None:
        keychain = __salt__['user.info'](user)['home'] + '/Library/Keychains/login.keychain-db'

    _, num = _get_account(name, url, user)

    ret_sum = 0
    for s in [name, name + '_app-password']:
        ret = __salt__['cmd.retcode'](
            "/usr/bin/security find-generic-password -a '{}:{}/:{}' -s 'Nextcloud' '{}'".format(
                s, url, num, keychain))
        ret_sum += ret

    # since there are two possible names, but both are written by nextcloud
    # (not sure if both are necessary), only return success if both are found
    return ret_sum == 0


def _macos_save_authentication(name, app_password, url, keychain=None, user=None):
    if _macos_has_authentication(name, url, keychain, user):
        raise CommandExecutionError("An item for account {} on server {} already exists in keychain {} for user {}.".format(name, url, keychain, user))

    if keychain is None:
        keychain = __salt__['user.info'](user)['home'] + '/Library/Keychains/login.keychain-db'

    _, num = _get_account(name, url, user)
    for s in [name, name + '_app-password']:
        # do not run as different user since switching context during salt run
        # results in denied requests: SecKeychainItemCreateFromContent
        # "user interaction is not allowed"
        ret = __salt__['cmd.run'](
            "/usr/bin/security add-generic-password -a '{}:{}/:{}' -s 'Nextcloud' -T '/Applications/Nextcloud.app' -w '{}' '{}'".format(
                s, url, num, app_password, keychain))
        if ret:
            raise CommandExecutionError("Could not save the application password for {} on {} to keychain {} for user {}.".format(name, url, keychain, user))
    return app_password


def _macos_delete_authentication(name, url, keychain=None, user=None):
    if not _macos_has_authentication(name, url, keychain, user):
        raise CommandExecutionError("An item for account {} on server {} does not exist in keychain {} for user {}.".format(name, url, keychain, user))

    _, num = _get_account(name, url, user)
    if keychain is None:
        keychain = __salt__['user.info'](user)['home'] + '/Library/Keychains/login.keychain-db'

    for s in [name, name + '_app-password']:
        ret = __salt__['cmd.run'](
            "/usr/bin/security delete-generic-password -a '{}:{}/:{}' -s 'Nextcloud' '{}'".format(
                s, url, num, keychain))
        if 'password has been deleted.' not in ret:
            raise CommandExecutionError("Could not remove the application password for {} on {} from keychain {} for user {}.".format(name, url, keychain, user))
    return True


def _macos_get_authentication(name, url, keychain=None, user=None):
    if not _macos_has_authentication(name, url, keychain, user):
        raise CommandExecutionError("An item for account {} on server {} does not exist in keychain {} for user {}.".format(name, url, keychain, user))
    _, num = _get_account(name, url, user)
    if keychain is None:
        keychain = __salt__['user.info'](user)['home'] + '/Library/Keychains/login.keychain-db'

    cmd = "/usr/bin/security find-generic-password -a '{}:{}/:{}' -s 'Nextcloud' -w '{}'".format(
              name, url, num, keychain)

    ret = __salt__['cmd.run'](cmd)

    if ret:
        return ret
    raise CommandExecutionError("Could not get authentication data for {} on {} in keychain {} for user {}.".format(name, url, keychain, user))


def _list_accounts(user=None):
    c = _get_parsed_cfg(user)
    return [x[1] for x in c.items('Accounts') if '\\dav_user' in x[0]]


def _get_account(name, url=None, user=None):
    for i, x in _get_accounts(user).items():
        if name == x['dav_user']:
            if url is None or url == x['url']:
                return x, i
    raise CommandExecutionError("Could not find account named {} on {} in nextcloud.cfg for user {}.".format(name, url, user))


def _get_accounts(user=None):
    c = _get_parsed_cfg(user)
    accs = {}
    for setting in c.items('Accounts'):
        # filter
        # there is a setting called 'user', but it seems to contain @Invalid() only
        for interesting in ['\\authtype', '\\dav_user', '\\http_user', '\\url']:
            if interesting in setting[0]:
                i, s = setting[0].split('\\')
                i = int(i)
                if not accs.get(i):
                    accs[i] = {}
                accs[i][s] = setting[1]
    return accs


def _serialize_account(name, url, authtype='webflow', user=None):
    # user=@Invalid() seems to be important, without it, no account name
    # is shown and nextcloud does not recognize the credentials in the keychain
    account = {
        'authtype': authtype,
        'dav_user': name,
        'url': url,
        'user': '@Invalid()'
    }

    if 'webflow' == authtype:
        account.update({'webflow_user': name})
    elif 'http' == authtype:
        account.update({'http_user': name})
    else:
        raise CommandExecutionError("Unsupported authentication type {} for account {} on {} for user {}.".format(authtype, name, url, user))

    num = max(_get_accounts(user).keys() or [-1]) + 1

    # prepend <num>\ to keys and return
    return dict(zip(
        [str(num) + '\\' + x for x in account.keys()],
        account.values()))


def _get_parsed_cfg(user=None):
    cfg = _where(user)
    c = configparser.ConfigParser()
    # case-sensitive read/write. configparser defaults to insensitive
    # can be set to any function and parses on read/write
    c.optionxform = str
    if __salt__['file.file_exists'](cfg):
        c.read(cfg)
    if not c.has_section('Accounts'):
        c.add_section('Accounts')
    return c


def _update_cfg(section, options, c=None, user=None):
    if c is None:
        c = _get_parsed_cfg(user)

    section = str(section)

    if not section == configparser.DEFAULTSECT and \
       not c.has_section(section):
        c.add_section(section)

    for opt, val in options.items():
        opt, val = str(opt), str(val)
        c[section][opt] = val

    return c


def _save_cfg(c, user=None):
    with open(_where(user), 'w') as f:
        c.write(f, space_around_delimiters=False)
    return True
