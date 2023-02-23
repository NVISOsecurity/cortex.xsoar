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
module: xsoar_multi_tenant_sync_accounts
short_description: Sync all content to all accounts in a multi-tenant Palo Alto Cortex XSOAR environment
version_added: "1.0.0"
description: Sync all content to all accounts in a multi-tenant Palo Alto Cortex XSOAR environment
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    timeout:
        description: The timout in seconds of the Sync All request
        required: false
        type: int
        default: 300
    url:
        description: URL of Palo Alto Cortex XSOAR.
        required: true
        type: str
    api_key:
        description: API Key to connect to Palo Alto Cortex XSOAR.
        required: true
        type: str
    validate_certs: 
        description:
          - If false, SSL certificates will not be validated.
          - This should only set to false used on personally controlled sites using self-signed certificates.
        required: false
        type: bool
        default: true

extends_documentation_fragment:
    - cortex.xsoar.xsoar_multi_tenant_sync_accounts

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Sync all content to all accounts in a multi-tenant Palo Alto Cortex XSOAR environment with untrusted SSL certificates
- name: Sync content to all accounts
  cortex.xsoar.xsoar_multi_tenant_sync_accounts:
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False
    
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_multi_tenant_sync_accounts module generates.
    type: str
    returned: on change
    sample: 'All Accounts synced in Palo Alto Cortex XSOAR'
'''


class CortexXSOARSyncAll:
    def __init__(self, module):
        self.module = module
        self.base_url = module.params['url']
        self.api_key = module.params['api_key']
        self.validate_certs = module.params['validate_certs']
        self.headers = {
            "Authorization": f"{self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.timeout = module.params['timeout']

    def sync_all_accounts(self):
        url_suffix = "accounts/content/sync"

        url = f'{self.base_url}/{url_suffix}'

        data = {}

        json_data = json.dumps(data, ensure_ascii=False)

        try:
            if not self.module.check_mode:
                open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs,
                         timeout=self.timeout)
            return 0, f"All Accounts synced in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to sync all Accounts", f"Error creating list: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=300),
        ),
        supports_check_mode=True
    )

    client = CortexXSOARSyncAll(module)

    result = {
        'name': 'Sync all Accounts'
    }

    rc, msg, err = client.sync_all_accounts()

    if rc is not None and rc != 0:
        module.fail_json(name="Sync all Accounts", msg=err)

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
