# Ansible Role freeipa_server

This role installs and configures [FreeIPA](https://www.freeipa.org/) as a server.

FQCN: linuxfabrik.lfops.freeipa_server

Tested on

* RHEL 8 (and compatible)


## Requirements

## Mandatory

* Install the [ansible-freeipa Ansible Collection](https://github.com/freeipa/ansible-freeipa) on the Ansible control node. For example by calling `ansible-galaxy collection install freeipa.ansible_freeipa`.


## Optional

This role does not have optional requirements.


## Tags

| Tag            | What it does                    |
| ---            | ------------                    |
| freeipa_server | Installs and configures freeipa |



## Role Variables

Have a look at the available role variables from the [freeipa.ansible_freeipa.ipaserver Role](https://github.com/freeipa/ansible-freeipa/tree/master/roles/ipaserver#variables).


### Mandatory


#### ipadm_password

Password for the Directory Manager.

Example:
```yaml
ipadm_password: 'password'
```


#### ipaadmin_password

Password for the IPA admin user.

Default:
```yaml
ipaadmin_password: 'password'
```


### Optional

#### ipaserver_domain

The primary DNS domain.

Default:
```yaml
ipaserver_domain: '{{ hostname__domain_name | lower }}'
```


#### ipaserver_realm

The Kerberos realm.

Default:
```yaml
ipaserver_realm: '{{ hostname__domain_name | upper }}'
```


#### ipaserver_setup_firewalld

If the needed services should automatically be opened in the firewall managed by firewalld.

Default:
```yaml
ipaserver_setup_firewalld: false
```


## License

[The Unlicense](https://unlicense.org/)


## Author Information

[Linuxfabrik GmbH, Zurich](https://www.linuxfabrik.ch)
