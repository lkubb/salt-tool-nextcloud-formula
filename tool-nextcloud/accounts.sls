{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

include:
  - .package

{%- for user in nextcloud.users | selectattr('nextcloud.accounts', 'defined') %}
  {%- for account in user.nextcloud.accounts %}
Nextcloud user account '{{ account.name }}' is present in {{ user.name }}'s config:
  nextcloud.account_present:
    - name: {{ account.name }}
    - url: {{ account.url }}
    - authtype: {{ account.get('authtype', 'webflow') }}

    {%- if 'Darwin' == grains['kernel'] and (account.get('password') or account.get('password_pillar')) %}
Nextcloud user account '{{ account.name }}' is authenticated for {{ user.name }}:
  nextcloud.account_authenticated:
    - name: {{ account.name }}
    - url: {{ account.url }}
      {%- if account.get('password') %}
    - password: {{ account.password }}
      {%- elif account.get('password_pillar') %}
    - password_pillar: {{ account.password_pillar }}
      {%- endif %}
    - user: {{ user.name }}
    - require:
      - Nextcloud user account '{{ account.name }}' is present in {{ user.name }}'s config
    {%- endif %}
  {%- endfor %}
{%- endfor %}
