# -*- coding: utf-8 -*-
# vim: ft=sls

{#- Get the `tplroot` from `tpldir` #}
{%- set tplroot = tpldir.split('/')[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}


{%- for user in nextcloud.users | selectattr('nextcloud.accounts', 'defined') | selectattr('nextcloud.accounts') %}

{%-   for account in user.nextcloud.accounts %}
Nextcloud user account '{{ account.name }}' is absent from {{ user.name }}'s config:
  nextcloud.account_absent:
    - name: {{ account.name }}
    - url: {{ account.url }}
    - user: {{ user.name }}

{%-     if 'Darwin' == grains['kernel'] and (account.get('password') or account.get('password_pillar')) %}

Nextcloud user account '{{ account.name }}' is authenticated for {{ user.name }}:
  nextcloud.account_deauthenticated:
    - name: {{ account.name }}
    - url: {{ account.url }}
    - prompt: true
    - user: {{ user.name }}
    - require:
      - Nextcloud user account '{{ account.name }}' is absent from {{ user.name }}'s config
{%-     endif %}
{%-   endfor %}
{%- endfor %}
