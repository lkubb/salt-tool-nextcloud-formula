# -*- coding: utf-8 -*-
# vim: ft=sls

{%- set tplroot = tpldir.split('/')[0] %}
{%- set sls_config_clean = tplroot ~ '.config.clean' %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}

include:
  - {{ sls_config_clean }}


Nextcloud Desktop is removed:
  pkg.removed:
    - name: {{ nextcloud.lookup.pkg.name }}
    - require:
      - sls: {{ sls_config_clean }}
