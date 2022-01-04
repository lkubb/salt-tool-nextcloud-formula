{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

include:
  - .package
{%- if nextcloud.users | selectattr('nextcloud.config', 'defined') %}
  - .config
{%- endif %}
{%- if nextcloud.users | selectattr('nextcloud.accounts', 'defined') %}
  - .accounts
{%- endif %}
