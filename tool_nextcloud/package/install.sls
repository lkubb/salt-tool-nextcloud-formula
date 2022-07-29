# -*- coding: utf-8 -*-
# vim: ft=sls

{%- set tplroot = tpldir.split('/')[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}


# @TODO Linux/Windows (?)
# For Linux, there is an AppImage.
Nextcloud Desktop is installed:
  pkg.installed:
    - name: {{ nextcloud.lookup.pkg.name }}

{%- for user in nextcloud.users %}

# needed for the execution module
Nextcloud config file exists for user '{{ user.name }}':
  file.managed:
    - name: {{ user._nextcloud.conffile }}
    - user: {{ user.name }}
    - group: {{ user.group }}
    - replace: false
    - mode: '0600'
    - dir_mode: '0700'
    - makedirs: true
    - require_in:
      - Nextcloud Desktop setup is completed
{%- endfor %}

Nextcloud Desktop setup is completed:
  test.nop:
    - name: Hooray, Nextcloud Desktop setup has finished.
    - require:
      - pkg: {{ nextcloud.lookup.pkg.name }}
