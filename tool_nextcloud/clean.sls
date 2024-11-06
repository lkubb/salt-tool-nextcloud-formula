# vim: ft=sls

{#-
    *Meta-state*.

    Undoes everything performed in the ``tool_nextcloud`` meta-state
    in reverse order.
#}

include:
  - .accounts.clean
  - .config.clean
  - .package.clean
