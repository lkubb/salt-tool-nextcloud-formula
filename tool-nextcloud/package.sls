{%- from 'tool-nextcloud/map.jinja' import nextcloud -%}

Nextcloud Desktop is installed:
  pkg.installed:
    - name: {{ nextcloud.package }}
