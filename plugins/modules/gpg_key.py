#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Linuxfabrik GmbH, Zurich, Switzerland, https://www.linuxfabrik.ch
# The Unlicense (see LICENSE or https://unlicense.org/)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
module: gpg_key

short_description: Create and fetch GPG keys

description:
    - This Ansible module returns a GPG key by listing all available key on the host and matching them with the given options.
    - If no GPG key is found, a new one is generated with the given options.
    - This module heavily relies on the U(https://github.com/vsajip/python-gnupg) library.
    - On success, this module returns the GPG private key as described L(here,https://gnupg.readthedocs.io/en/latest/#listing-keys). The output is augmented with the armored ASCII representation of both the private and public key.

notes:
    - When checking if there is an existing GPG key, we match it using all the provided options, besides the passphrase.
    - However, if there is a subkey option specified, and there is a key with multiple subkey present, only one has to match for us to assume that it is the correct key.
    - This module currently only provides a small subset of the available GPG options. If you require more, issues and pull requests are very welcome.

requirements:
    - Requires the GNU Privacy Guard command line tool C(gpg).

author:
    - Linuxfabrik GmbH, Zurich, Switzerland, https://www.linuxfabrik.ch

version_added: "1.0.0"

options:
    gnupghome:
        description: The path to the gnupg directory.
        required: False
        default: What gpg itself would use, for example on RHEL ~/.gnupg
    gpgbinary:
        description: The explicit executable or pathname for the C(gpg) executable.
        required: False
        default: gpg
    key_length:
        description: The length used for the GPG key.
        required: False
        default: 1024
    key_type:
        description: The type (algorithm) used for the GPG key.
        required: False
        default: RSA
    name_comment:
        description: The comment used for the GPG key.
        required: False
        default: Generated by Ansible.
    name_email:
        description: The email used for the GPG key.
        required: False
        default: info@example.com
    name_real:
        description: The name used for the GPG key.
        required: False
        default: Autogenerated Key
    passphrase:
        description: The passphrase used for the GPG key.
        required: False
    subkey_length:
        description: The length used for the GPG subkey.
        required: False
    subkey_type:
        description: The type (algorithm) used for the GPG subkey.
        required: False
'''

EXAMPLES = r'''
- name: 'Generate a GPG key by using the defaults'
  linuxfabrik.lfops.gpg_key:
  register: gpg_key

- ansible.builtin.debug:
    var: gpg_key

- name: 'Generate gpg key'
  linuxfabrik.lfops.gpg_key:
    name_real: 'My name'
    name_email: '{{ ansible_facts["user_id"] }}@{{ ansible_facts["nodename"] }}'
    key_type: 'RSA'
    key_length: 4096
    passphrase: 'secret-passphrase'
    subkey_type: 'RSA'
    subkey_length: 4096
  register: gpg_key
'''

RETURN = r'''
ascii_armored_private_key:
    description: The exported armored ascii representation of both the private key.
    returned: success
    type: str
    sample: '-----BEGIN PGP PRIVATE KEY BLOCK-----\n\n...\n-----END PGP PRIVATE KEY BLOCK-----\n'
ascii_armored_public_key:
    description: The exported armored ascii representation of both the public key.
    returned: success
    type: str
    sample: '-----BEGIN PGP PUBLIC KEY BLOCK-----\n\n...\n-----END PGP PUBLIC KEY BLOCK-----\n'
algo:
    description: The GPG key.
    returned: success
    type: dict
    contains:
        algo:
            description: Public key algorithm.
            returned: success
            type: int
            sample: 1
        cap:
            description: Key capabilities.
            returned: success
            type: str
            sample: escaESCA
        compliance:
            description: Compliance flags.
            returned: success
            type: str
            sample: ''
        curve:
            description: Curve name for elliptic curve cryptography (ECC) keys.
            returned: success
            type: str
            sample: ''
        date:
            description: The creation date of the key in UTC as a Unix timestamp.
            returned: success
            type: int
            sample: 1645019144
        dummy:
            description: Certificate serial number, UID hash or trust signature info.
            returned: success
            type: str
            sample: ''
        expires:
            description: The expiry date of the key in UTC as a timestamp, if specified.
            returned: success
            type: str
            sample: ''
        fingerprint:
            description: The fingerprint of the key.
            returned: success
            type: str
            sample: ECA3505F5A6F61A528D6A5087EFF958551A5481E
        flag:
            description: A flag field.
            returned: success
            type: str
            sample: ''
        hash:
            description: Hash algorithm.
            returned: success
            type: str
            sample: ''
        issuer:
            description: Issuer information.
            returned: success
            type: str
            sample: ''
        keyid:
            description: The key ID.
            returned: success
            type: str
            sample: 7EFF958551A5481E
        length:
            description: The length of the key in bits.
            returned: success
            type: int
            sample: 1024
        origin:
            description: Origin of keys.
            returned: success
            type: int
            sample: 0
        ownertrust:
            description: The level of owner trust for the key.
            returned: success
            type: str
            sample: u
        sig:
            description: Signature class.
            returned: success
            type: str
            sample: ''
        subkey_info:
            description: A dictionary of subkey information keyed on subkey id.
            returned: success
            type: dict
        subkeys:
            description: A list containing [keyid, type] elements for each subkey.
            returned: success
            type: list
            sample:
                - 524C9D5EB862A934
                - null
                - D002B0EB3BF40CF209930E74524C9D5EB862A934
        token:
            description: Token serial number.
            returned: success
            type: str
            sample: +
        trust:
            description: The validity of the key.
            returned: success
            type: str
            sample: u
        type:
            description: Type of key.
            returned: success
            type: str
            sample: sec
        uid:
            description: The user ID.
            returned: success
            type: list
            sample: ['Autogenerated Key (Generated by Ansible.) <info@example.com>']
        updated:
            description: Last updated timestamp.
            returned: success
            type: str
            sample: ''
'''

import logging
import os
import re
import traceback

logger = logging.getLogger('gnupg')
logger.setLevel(logging.DEBUG)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.linuxfabrik.lfops.plugins.module_utils.gnupg import GPG

# taken from https://www.iana.org/assignments/pgp-parameters/pgp-parameters.xhtml#pgp-parameters-12
algo_ids = {
    1: 'RSA',
    2: 'RSA',
    3: 'RSA',
    16: 'Elgamal',
    17: 'DSA',
    18: 'ECDH',
    19: 'ECDSA',
}

name_email_regex = re.compile(r' <(.*)>$')
name_comment_regex = re.compile(r' \((.*)\)')


def match_key(key, params):
    if algo_ids.get(int(key['algo']), 'Unknown') != params['key_type']:
        return False

    if int(key['length']) != params['key_length']:
        return False

    # we assume that there can only be one uid, as we couldn't find anything contradicting that
    uid = key['uids'][0].strip()
    name_real_end = len(uid)

    name_email_match = name_email_regex.search(uid)
    name_email = None
    if name_email_match:
        name_email = name_email_match.group(1)
        name_real_end = name_email_match.start()

    if name_email != params['name_email']:
        return False

    name_comment_match = name_comment_regex.search(uid)
    name_comment = None
    if name_comment_match:
        name_comment = name_comment_match.group(1)
        name_real_end = name_comment_match.start()

    if name_comment != params['name_comment']:
        return False

    name_real = uid[:name_real_end]

    if name_real != params['name_real']:
        return False

    if 'subkey_info' in key:
        # if there is at least one matching subkey, we assume a match. the unattended creation can only create a single subkey,
        # howerever, it is possible to add another one manually later.
        first_subkey_match = None
        for subkey_id, subkey in key['subkey_info'].items():

            if algo_ids.get(int(subkey['algo']), 'Unknown') != params['subkey_type']:
                continue

            if int(subkey['length']) != params['subkey_length']:
                continue

            first_subkey_match = subkey

        if not first_subkey_match:
            return False

    return True


def add_armored_exports_and_exit(gpg, module, result):
    ascii_armored_private_key = gpg.export_keys(result['key']['fingerprint'], secret=True, passphrase=module.params['passphrase'])
    if not ascii_armored_private_key:
        # sadly, we do not get more information from the library
        module.fail_json(msg='Failed to export armored private key. Is the passphrase correct?', **result)
    result['ascii_armored_private_key'] = ascii_armored_private_key

    ascii_armored_public_key = gpg.export_keys(result['key']['fingerprint'], passphrase=module.params['passphrase'])
    result['ascii_armored_public_key'] = ascii_armored_public_key
    module.exit_json(**result)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        gpgbinary=dict(type='str', required=False, default='gpg'),
        gnupghome=dict(type='str', required=False),

        name_real=dict(type='str', required=False, default='Autogenerated Key'),
        name_comment=dict(type='str', required=False, default='Generated by Ansible.'),
        name_email=dict(type='str', required=False, default='info@example.com'),

        key_type=dict(type='str', required=False, default='RSA'),
        key_length=dict(type='int', required=False, default=1024),

        passphrase=dict(type='str', required=False, default='', no_log=True),

        subkey_type=dict(type='str', required=False),
        subkey_length=dict(type='int', required=False),
    )

    result = dict(
        changed=False,
        key=None,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if debug
    # console_logger = logging.StreamHandler()
    # console_logger.setLevel(logging.DEBUG)
    # console_logger.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    # logger.addHandler(console_logger)

    gnupghome = module.params['gnupghome']
    if gnupghome and not os.path.isdir(gnupghome):

        if module.check_mode:
            # since there is no directory, there are no keys - meaning we have to generate one for sure. set to changed but do not do anything
            result['changed'] = True
            module.exit_json(**result)

        os.makedirs(gnupghome, 0o700)

    try:
        gpg = GPG(
            gpgbinary=module.params['gpgbinary'],
            gnupghome=gnupghome,
        )
    except (OSError, ValueError) as e:
        module.fail_json(msg='There was an error executing gpg: {}'.format(to_native(e)), exception=traceback.format_exc(), **result)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target

    keys = gpg.list_keys(secret=True)
    if keys.returncode != 0:
        module.fail_json(msg='Failed to list current keys.', rc=keys.returncode, stdout=keys.data, stderr=keys.stderr, **result)

    # do match on all given arguments except for passphrase (as we do not see that one).
    match = None
    for key in keys:
        matched = match_key(key, module.params)
        if matched:
            if match is None:
                match = key
            else:
                module.fail_json(msg='Found multiple keys with the same attributes, cannot decide which one to use. Aborting.', **result)

    if match:
        result['key'] = match
        add_armored_exports_and_exit(gpg, module, result)
    else:
        # set changed before quitting in check mode to indicate that we would generate a new key
        result['changed'] = True

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    params = {k: v for k, v in module.params.items() if v is not None}
    params.pop('gnupghome', None) # provide default to prevent KeyError
    params.pop('gpgbinary', None) # provide default to prevent KeyError
    if not module.params['passphrase']:
        params['no_protection'] = True

    input_data = gpg.gen_key_input(**params)
    # print(params)
    # print(input_data)
    new_key = gpg.gen_key(input_data)
    if not new_key:
        module.fail_json(msg='Failed to generate a new key.', rc=new_key.returncode, stdout=new_key.data, stderr=new_key.stderr, input_data=input_data, **result)

    # list the keys again, as we only got the fingerprint from gen_key()
    keys = gpg.list_keys(secret=True)
    if keys.returncode != 0:
        module.fail_json(msg='Failed to list current keys.', rc=keys.returncode, stdout=keys.data, stderr=keys.stderr, **result)

    for key in keys:
        if key['fingerprint'] == new_key.fingerprint:
            result['key'] = key
            break

    if not result['key']:
        module.fail_json(msg='Could not find the newly generated key.', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    add_armored_exports_and_exit(gpg, module, result)


def main():
    run_module()


if __name__ == '__main__':
    main()
