# -*- coding: utf-8 -*-
# vim: ft=sls

{#- Get the `tplroot` from `tpldir` #}
{%- set tplroot = tpldir.split('/')[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}


{%- for user in nextcloud.users | selectattr('nextcloud.config', 'defined') | selectattr('nextcloud.config') %}

Nextcloud Desktop config file is cleaned for user '{{ user.name }}':
  file.absent:
    - name: {{ user['_nextcloud'].conffile }}
{%- endfor %}
