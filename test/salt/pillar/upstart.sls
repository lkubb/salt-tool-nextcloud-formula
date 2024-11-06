# vim: ft=yaml
---
tool_global:
  users:
    user:
      completions: .completions
      configsync: true
      persistenv: .bash_profile
      rchook: .bashrc
      xdg: true
      nextcloud:
        accounts:
          - name: nextcloud-common-user
            password: mediocre_nextcloud-password...
            password_pillar: tool:nextcloud:password
            url: https://cloud.test.com
        config:
          General:
            optionalServerNotifications: 'false'
        sync_config: false
tool_nextcloud:
  lookup:
    master: template-master
    # Just for testing purposes
    winner: lookup
    added_in_lookup: lookup_value

    pkg:
      name: nextcloud
    paths:
      confdir: '.config/nextcloud'
      conffile: 'nextcloud.cfg'
      xdg_dirname: 'nextcloud'
      xdg_conffile: 'nextcloud.cfg'
    rootgroup: root

  tofs:
    # The files_switch key serves as a selector for alternative
    # directories under the formula files directory. See TOFS pattern
    # doc for more info.
    # Note: Any value not evaluated by `config.get` will be used literally.
    # This can be used to set custom paths, as many levels deep as required.
    files_switch:
      - any/path/can/be/used/here
      - id
      - roles
      - osfinger
      - os
      - os_family
    # All aspects of path/file resolution are customisable using the options below.
    # This is unnecessary in most cases; there are sensible defaults.
    # path_prefix: template_alt
    # dirs:
    #   files: files_alt
    #   default: default_alt
    # The entries under `source_files` are prepended to the default source files
    # given for the state
    # source_files:
    #   tool-nextcloud-config-file-file-managed:
    #     - 'example_alt.tmpl'
    #     - 'example_alt.tmpl.jinja'

    # For testing purposes
    source_files:
      Nextcloud Desktop config file is managed for user 'user':
        - 'nextcloud.cfg'
        - 'nextcloud.cfg.jinja'

  # Just for testing purposes
  winner: pillar
  added_in_pillar: pillar_value
