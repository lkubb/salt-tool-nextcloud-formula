# Nextcloud Desktop Formula
Sets up and configures Nextcloud Desktop client, including user accounts and authentication on setup (for MacOS only currently).

## Usage
Applying `tool-nextcloud` will make sure Nextcloud Desktop client is configured as specified.

### Execution module and state
This formula provides a relatively large custom execution module and state to manage user accounts, their authentication and general Nextcloud options in `nextcloud.cfg`. The functions are documented, please see the source code for comments. Currently, the following states are supported:
* `nextcloud.account_present(name, url, authtype='webflow', user=None)`
* `nextcloud.account_absent(name, url=None, user=None)`
* `nextcloud.account_authenticated(name, url=None, password=None, password_pillar=None, keyring=None, user=None)`
* `nextcloud.account_deauthenticated(name, url=None, app_password=None, keyring=None, prompt=True, user=None)`
* `nextcloud.options(options, sync=False, sync_accounts=False, user=None)`

## Configuration
### Pillar
#### General `tool` architecture
Since installing user environments is not the primary use case for saltstack, the architecture is currently a bit awkward. All `tool` formulas assume running as root. There are three scopes of configuration:
1. per-user `tool`-specific
  > e.g. generally force usage of XDG dirs in `tool` formulas for this user
2. per-user formula-specific
  > e.g. setup this tool with the following configuration values for this user
3. global formula-specific (All formulas will accept `defaults` for `users:username:formula` default values in this scope as well.)
  > e.g. setup system-wide configuration files like this

**3** goes into `tool:formula` (e.g. `tool:git`). Both user scopes (**1**+**2**) are mixed per user in `users`. `users` can be defined in `tool:users` and/or `tool:formula:users`, the latter taking precedence. (**1**) is namespaced directly under `username`, (**2**) is namespaced under `username: {formula: {}}`.

```yaml
tool:
######### user-scope 1+2 #########
  users:                         #
    username:                    #
      xdg: true                  #
      dotconfig: true            #
      formula:                   #
        config: value            #
####### user-scope 1+2 end #######
  formula:
    formulaspecificstuff:
      conf: val
    defaults:
      yetanotherconfig: somevalue
######### user-scope 1+2 #########
    users:                       #
      username:                  #
        xdg: false               #
        formula:                 #
          otherconfig: otherval  #
####### user-scope 1+2 end #######
```

#### User-specific
The following shows an example of `tool-nextcloud` pillar configuration. Namespace it to `tool:users` and/or `tool:nextcloud:users`.
```yaml
user:
  nextcloud:
    # these are configuration options in nextcloud.cfg. Section: {option: value}
    config:
      General:
        optionalServerNotifications: true
    # you can specify adding accounts as well. if password[_pillar] is set, salt
    # will try to authenticate them automatically and save to the system keyring
    # currently only supported on MacOS
    accounts:
      - name: nextcloud-user
        url: https://cloud.test.com          # no trailing slash
        password: super_nextcloud-password!  # better use password_pillar instead
        password_pillar: 'tool:users:user:nextcloud:password' # avoids disk writes (state cache)
```

#### Formula-specific
```yaml
tool:
  nextcloud:
    defaults:                           # default formula configuration for all users
      config:
        General:
          optionalServerNotifications: false
      accounts:                         # accounts are currently not merged with default ones
        - name: nextcloud-common-user
          url: https://cloud.test.com
          password: mediocre_nextcloud-password...
          password_pillar: 'tool:nextcloud:password'
```

## Todo
- default url in map.jinja
