# -*- coding: utf-8 -*-
# vim: ft=sls

{#- Get the `tplroot` from `tpldir` #}
{%- set tplroot = tpldir.split('/')[0] %}
{%- set sls_package_install = tplroot ~ '.package.install' %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}

include:
  - {{ sls_package_install }}


{%- for user in nextcloud.users | selectattr('nextcloud.accounts', 'defined') | selectattr('nextcloud.accounts') %}

{%-   for account in user.nextcloud.accounts %}
Nextcloud user account '{{ account.name }}' is present in {{ user.name }}'s config:
  nextcloud.account_present:
    - name: {{ account.name }}
    - url: {{ account.url }}
    - authtype: {{ account.get('authtype', 'webflow') }}
    - user: {{ user.name }}
    - require:
      - sls: {{ sls_package_install }}

{%-     if 'Darwin' == grains['kernel'] and (account.get('password') or account.get('password_pillar')) %}

Nextcloud user account '{{ account.name }}' is authenticated for {{ user.name }}:
  nextcloud.account_authenticated:
    - name: {{ account.name }}
    - url: {{ account.url }}
{%-       if account.get('password') %}
    - password: {{ account.password }}
{%-       elif account.get('password_pillar') %}
    - password_pillar: {{ account.password_pillar }}
{%-       endif %}
    - user: {{ user.name }}
    - require:
      - Nextcloud user account '{{ account.name }}' is present in {{ user.name }}'s config
{%-     endif %}
{%-   endfor %}
{%- endfor %}
