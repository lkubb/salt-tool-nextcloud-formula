{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

include:
  - .package

{%- for user in nextcloud.users | selectattr('nextcloud.config', 'defined') %}
Nextcloud Desktop configuration is synced for user '{{ user.name }}':
  nextcloud.options:
    - options: {{ user.nextcloud.config | json }}
    - sync: {{ user.nextcloud.get('sync_config', False) }}
    - sync_accounts: False
    - user: {{ user.name }}
{%- endfor %}
