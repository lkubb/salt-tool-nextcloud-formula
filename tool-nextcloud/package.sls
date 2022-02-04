{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

Nextcloud Desktop is installed:
  pkg.installed:
    - name: {{ nextcloud.package }}

{%- for user in nextcloud.users %}

Nextcloud config file exists for user '{{ user.name }}':
  file.managed:
    - name: {{ user._nextcloud.confdir }}/nextcloud.cfg
    - user: {{ user.name }}
    - group: {{ user.group }}
    - replace: false
    - mode: '0600'
    - dir_mode: '0700'
    - makedirs: true
{%- endfor %}
