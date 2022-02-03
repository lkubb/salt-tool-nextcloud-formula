{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

Nextcloud Desktop is installed:
  pkg.installed:
    - name: {{ nextcloud.package }}

{%- for user in nextcloud.users %}

Nextcloud config folder exists for user '{{ user.name }}':
  file.directory:
    - name: {{ user._nextcloud.confdir }}
    - user: {{ user.name }}
    - group: {{ user.group }}
    - mode: '0700'
{%- endfor %}
