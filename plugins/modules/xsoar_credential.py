#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

__metaclass__ = type

DOCUMENTATION = r'''
---
module: xsoar_credential
short_description: Create a Credential in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create a Credential in Palo Alto Cortex XSOAR
notes:
  - Tested against Palo Alto Cortex XSOAR 6.13 (B1284375).
options:
    name:
        description: Name of the Credential.
        required: true
        type: str
    user:
        description: Username to be stored in the Credential.
        required: false
        type: str
    password:
        description: Password to be stored in the Credential.
        required: false
        type: str
    workgroup:
        description: Workgroup to be stored in the Credential.
        required: false
        type: str
    certificate:
        description: Certificate to be stored in the Credential.
        required: false
        type: str
    state:
        description: The state the configuration should be left in.
        required: true
        type: str
        choices:
          - present
          - absent
        default: present
    url:
        description: URL of Palo Alto Cortex XSOAR.
        required: true
        type: str
    api_key:
        description: API Key to connect to Palo Alto Cortex XSOAR.
        required: true
        type: str
    account: Account in a Palo Alto Cortex XSOAR multi-tenant environment.
        description: 
        required: false
        type: str
    validate_certs: 
        description:
          - If false, SSL certificates will not be validated.
          - This should only set to false used on personally controlled sites using self-signed certificates.
        required: false
        type: bool
        default: true

extends_documentation_fragment:
    - cortex.xsoar.xsoar_credential

author:
    - Jenda Brands (@jendab)
'''

EXAMPLES = r'''
# Create a Credential in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Store username/password/workgroup combination
  cortex.xsoar.xsoar_credential:
    name: "cred01"
    user: "username"
    password: "Banana123"
    workgroup: "workgroup01"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Create a credential in an account in a Palo Alto Cortex XSOAR multi-tenant environment while getting the password from Ansible Vault
- name: Create Configuration Text list in account Client01
  cortex.xsoar.xsoar_credential:
    name: "cred01"
    user: "username"
    password: "{{ vault.client01.cred01.password }}"  # assumes using an Ansible vault with this structure
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    
# Create a credential with certificate in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Configuration Text list in account Client01
  cortex.xsoar.xsoar_credential:
    name: "cred01"
    certificate: "{{ vault.client01.cred01.certificate }}"
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"

# Remove a list in Palo Alto Cortex XSOAR
- name: Remove credential "cred01"
  cortex.xsoar.xsoar_credential:
    name: "cred01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_credential module generates.
    type: str
    returned: on change
    sample: 'Credential created in Palo Alto Cortex XSOAR'
'''


class CortexXSOARCredential:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.user = module.params['user']
        self.password = module.params['password']
        self.workgroup = module.params['workgroup']
        self.certificate = module.params['certificate']
        self.state = module.params['state']
        self.base_url = module.params['url']
        self.api_key = module.params['api_key']
        self.account = module.params['account']
        self.validate_certs = module.params['validate_certs']
        self.headers = {
            "Authorization": f"{self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def exists(self):
        url_suffix = 'settings/credentials'
        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        data = {
            "page": 0,
            "query": "",
            "size": 200
        }

        json_data = json.dumps(data, ensure_ascii=False)

        response = open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, dict):
            return False

        xsoar_credentials = [credential for credential in results["credentials"] if credential.get('name') == self.name]

        if not len(xsoar_credentials) == 1:
            return False

        xsoar_credential = xsoar_credentials[0]

        if not xsoar_credential.get('id') == self.name:
            return False

        if self.user:
            if not xsoar_credential.get('user') == self.user:
                return False
            
        if self.workgroup:
            if not xsoar_credential.get('workgroup') == self.workgroup:
                return False
            
        if self.password:
            if not xsoar_credential.get('hasPassword'):
                return False
            
        if self.certificate:
            if not xsoar_credential.get('hasCertificate'):
                return False

        return True

    def add(self):
        url_suffix = 'settings/credentials'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        data = {
            "id": None,
            "version": 0,
            "name": self.name,
            "password": self.password,
            "sshkey": self.certificate,
            "user": self.user,
            "workgroup": self.workgroup,
            "hasPassword": bool(self.password),
            "hasCertificate": bool(self.certificate)
        }

        json_data = json.dumps(data, ensure_ascii=False)

        try:
            if not self.module.check_mode:
                open_url(url, method="PUT", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
            return 0, f"Credential {self.name} created in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to create credential {self.name}", f"Error creating credential: {str(e)}"

    def delete(self):
        url_suffix = "settings/credentials/delete"

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        data = {
            "id": self.name
        }

        json_data = json.dumps(data, ensure_ascii=False)

        try:
            if not self.module.check_mode:
                open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
            return 0, f"Credential {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete credential {self.name}", f"Error deleting credential: {str(e)}"

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            account=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
            user=dict(type='str', required=False, default=None),
            password=dict(type='str', required=False, default=None),
            workgroup=dict(type='str', required=False, default=None),
            certificate=dict(type='str', required=False, default=None)
        ),
        supports_check_mode=True
    )

    client = CortexXSOARCredential(module)

    rc = None
    msg = ''
    err = ''
    result = {
        'name': client.name,
        'state': client.state
    }

    if client.state == 'absent':
        if client.exists():
            rc, msg, err = client.delete()
    elif client.state == 'present':
        if not client.exists():
            rc, msg, err = client.add()
    if rc is not None and rc != 0:
        module.fail_json(name=client.name, msg=err)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if msg:
        result['msg'] = msg
    if err:
        result['stderr'] = err

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
