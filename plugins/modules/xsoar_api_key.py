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
module: xsoar_api_key
short_description: Create API Key in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create an API Key in Palo Alto Cortex XSOAR
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    name:
        description: Name of the API Key.
        required: true
        type: str
    key:
        description: API Key to set
        required: true
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
    - cortex.xsoar.xsoar_api_key

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Create an API Key in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Create API Key
  cortex.xsoar.xsoar_api_key:
    name: "API Key 01"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Create an API Key in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create API Key in account Client01
  cortex.xsoar.xsoar_api_key:
    name: "API Key 01"
    state: "present"
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"

# Remove an API Key in Palo Alto Cortex XSOAR
- name: Remove API Key "API Key 01"
  cortex.xsoar.xsoar_api_key:
    name: "API Key 01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_api_key module generates.
    type: str
    returned: on change
    sample: 'API Key API Key 01 deleted in Palo Alto Cortex XSOAR'
'''


class CortexXSOARAPIKey:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.state = module.params['state']
        self.base_url = module.params['url']
        self.api_key = module.params['api_key']
        self.account = module.params['account']
        self.key = module.params['key']
        self.validate_certs = module.params['validate_certs']
        self.headers = {
            "Authorization": f"{self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.id = None

    def exists(self):
        url_suffix = 'apikeys'
        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, list):
            return False

        xsoar_api_keys = [key for key in results if key.get('name') == self.name]

        if not len(xsoar_api_keys) == 1:
            return False

        xsoar_api_key = xsoar_api_keys[0]

        if not xsoar_api_key.get('name') == self.name:
            return False

        self.id = xsoar_api_key.get('id')

        return True

    def add(self):
        url_suffix = 'apikeys'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        data = {
            "name": self.name,
            "apikey": self.key
        }

        json_data = json.dumps(data, ensure_ascii=False)

        try:
            if not self.module.check_mode:
                open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
            return 0, f"API Key {self.name} created in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to create API Key {self.name}", f"Error creating API Key: {str(e)}"

    def delete(self):
        url_suffix = f"apikeys/{self.id}"

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        try:
            if not self.module.check_mode:
                open_url(url, method="DELETE", headers=self.headers, validate_certs=self.validate_certs)
            return 0, f"API Key {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete API Key {self.name}", f"Error deleting API Key: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            key=dict(type='str', required=True),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            account=dict(type='str'),
            validate_certs=dict(type='bool', default=True)
        ),
        supports_check_mode=True
    )

    client = CortexXSOARAPIKey(module)

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
