# vim: ft=sls

{#-
    Removes the configuration of the Nextcloud Desktop package.
#}

{%- set tplroot = tpldir.split("/")[0] %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}


{%- for user in nextcloud.users | selectattr("nextcloud.config", "defined") | selectattr("nextcloud.config") %}

Nextcloud Desktop config file is cleaned for user '{{ user.name }}':
  file.absent:
    - name: {{ user["_nextcloud"].conffile }}
{%- endfor %}
