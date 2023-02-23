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
module: xsoar_multi_tenant_account
short_description: Create an Account in a multi-tenant Palo Alto Cortex XSOAR environment
version_added: "1.0.0"
description: Create an Account in a multi-tenant Palo Alto Cortex XSOAR environment
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    name:
        description: Name of the account
        required: true
        type: str
    propagation_labels:
        description: Propagation labels to add to the account
        required: false
        type: list
        default: ["all"]
    account_roles:
        description: Roles to add to the account
        required: false
        type: list
        default: ["Administrator"]
    host_group_id:
        description: ID of the host to create the account
        required: false
        type: str
    host_name:
        description: Name of the host to create the account
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
    validate_certs: 
        description:
          - If false, SSL certificates will not be validated.
          - This should only set to false used on personally controlled sites using self-signed certificates.
        required: false
        type: bool
        default: true

extends_documentation_fragment:
    - cortex.xsoar.xsoar_list

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Create an account in a multi-tenant Palo Alto Cortex XSOAR environment with untrusted SSL certificates
- name: Create Client01 account
  cortex.xsoar.xsoar_multi_tenant_account:
    name: "Client01"
    propagation_labels: ["all"]
    host_name: "host01"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Remove an account in a multi-tenant Palo Alto Cortex XSOAR environment
- name: Remove account "Client01"
  cortex.xsoar.xsoar_multi_tenant_account:
    name: "Client01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_multi_tenant_account module generates.
    type: str
    returned: on change
    sample: 'Account Client01 created in Cortex XSOAR'
'''


class CortexXSOARAccount:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.propagation_labels = module.params['propagation_labels']
        self.account_roles = module.params['account_roles']
        self.sync_on_creation = module.params['sync_on_creation']
        self.host_group_id = module.params['host_group_id'] or ""
        self.host_name = module.params['host_name']
        self.timeout = module.params['timeout']
        self.state = module.params['state']
        self.base_url = module.params['url']
        self.api_key = module.params['api_key']
        self.validate_certs = module.params['validate_certs']
        self.headers = {
            "Authorization": f"{self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.account_found = False

        if self.host_name:
            self.host_group_id = self.get_host_id(self.host_name)

    def get_host_id(self, host_name: str):
        url_suffix = 'ha-groups'

        url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        host_id = None

        if results and isinstance(results, list):
            xsoar_hosts = [host for host in results if host.get('name').split(':')[0] == self.host_name]
            if xsoar_hosts and len(xsoar_hosts) == 1:
                xsoar_host = xsoar_hosts[0]
                if xsoar_host and isinstance(xsoar_host, dict):
                    host_id = xsoar_host.get('id')

        if not host_id:
            raise Exception(f'Could not find ID of Cortex XSOAR host {host_name}')

        return str(host_id)

    def exists(self):
        url_suffix = 'accounts'

        url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, list):
            return False

        xsoar_accounts = [acc for acc in results if acc.get('name') == f'acc_{self.name}']

        if not len(xsoar_accounts) == 1:
            return False

        xsoar_account = xsoar_accounts[0]

        if not xsoar_account.get('name') == f'acc_{self.name}':
            return False

        self.account_found = True

        if self.propagation_labels:
            if not xsoar_account.get('propagationLabels') == self.propagation_labels:
                return False

        if self.account_roles:
            if not xsoar_account.get('roles', {}).get('roles') == self.account_roles:
                return False

        return True

    def add(self):
        if not self.account_found:
            url_suffix = 'account'

            url = f'{self.base_url}/{url_suffix}'

            data = {
                "name": self.name,
                "accountRoles": self.account_roles,
                "propagationLabels": self.propagation_labels,
                "syncOnCreation": self.sync_on_creation,
                "hostGroupId": self.host_group_id
            }

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs,
                             timeout=self.timeout)
                return 0, f"Account {self.name} created in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to create account {self.name}", f"Error creating account: {str(e)}"
        else:
            url_suffix = f'account/update/acc_{self.name}'

            url = f'{self.base_url}/{url_suffix}'

            data = {
                "selectedRoles": self.account_roles,
                "selectedPropagationLabels": self.propagation_labels
            }

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Account {self.name} updated in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to update account {self.name}", f"Error updating account: {str(e)}"

    def delete(self):
        url_suffix = f"account/purge/acc_{self.name}"

        url = f'{self.base_url}/{url_suffix}'

        try:
            if not self.module.check_mode:
                open_url(url, method="DELETE", headers=self.headers, validate_certs=self.validate_certs,
                         timeout=self.timeout)
            return 0, f"Account {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete account {self.name}", f"Error deleting account: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            host_group_id=dict(type='str'),
            host_name=dict(type='str'),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            timeout=dict(type='int', default=300),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            propagation_labels=dict(type='list', default=["all"]),
            account_roles=dict(type='list', default=["Administrator"]),
            validate_certs=dict(type='bool', default=True),
            sync_on_creation=dict(type='bool', default=True)
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('host_group_id', 'host_name'),
        ],
    )

    client = CortexXSOARAccount(module)

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
