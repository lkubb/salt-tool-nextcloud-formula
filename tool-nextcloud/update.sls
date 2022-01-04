{%- from 'tool-nextcloud/map.jinja' import nextcloud %}

{%- set accounts = nextcloud.users | selectattr('nextcloud.accounts', 'defined') -%}
{%- set config = nextcloud.users | selectattr('nextcloud.config', 'defined') -%}

{%- if accounts or config %}
include:
  {%- if config %}
  - .config
  {%- endif %}
  {%- if accounts %}
  - .accounts
  {%- endif %}
{%- endif %}
