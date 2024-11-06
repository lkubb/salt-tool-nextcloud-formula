# vim: ft=sls

{%- set tplroot = tpldir.split("/")[0] %}
{%- set sls_package_install = tplroot ~ ".package.install" %}
{%- from tplroot ~ "/map.jinja" import mapdata as nextcloud with context %}

include:
  - {{ sls_package_install }}


{%- for user in nextcloud.users | selectattr("nextcloud.config", "defined") | selectattr("nextcloud.config") %}

Nextcloud Desktop configuration is synced for user '{{ user.name }}':
  nextcloud.options:
    - options: {{ user.nextcloud.config | json }}
    - sync: {{ user.nextcloud.get("sync_config", false) }}
    - sync_accounts: false
    - user: {{ user.name }}
    - require:
      - sls: {{ sls_package_install }}
{%- endfor %}
