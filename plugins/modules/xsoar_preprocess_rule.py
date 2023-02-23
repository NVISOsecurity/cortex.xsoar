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
module: xsoar_preprocess_rule
short_description: Create a Pre-process Rule in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create a Pre-process Rule in Palo Alto Cortex XSOAR
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    name:
        description: Name of the List.
        required: true
        type: str
    description:
        description: Description of the List.
        required: false
        type: str
    content:
        description: Content of List.
        required: false
        type: str
    json_content:
        description: Content of JSON List.
        required: false
        type: dict
    content_type:
        description: Type of list.
        type: str
        choices:
          - JSON
          - HTML
          - Text
          - Markdown
          - CSS
        default: Text
    propagation_labels:
        description: Propagation labels to add to the account
        required: false
        type: list
        default: ["all"]
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
    - cortex.xsoar.xsoar_list

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Create a Pre-process Rule in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Create Pre-process Rule
  cortex.xsoar.xsoar_preprocess_rule:
    name: "Rule01"
    action: "script"
    script_id: "0a724a50-135f-466b-8f35-bbb1c7724bdd"
    enabled: True
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Create a Pre-process Rule in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Pre-process Rule in account Client01
  cortex.xsoar.xsoar_preprocess_rule:
    name: "Rule01"
    action: "script"
    script_id: "0a724a50-135f-466b-8f35-bbb1c7724bdd"
    enabled: True
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"

# Remove a Pre-process Rule in Palo Alto Cortex XSOAR
- name: Remove Pre-process Rule "List01"
  cortex.xsoar.xsoar_preprocess_rule:
    name: "Rule01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_preprocess_rule module generates.
    type: str
    returned: on change
    sample: 'Pre-process rule Rule01 created in Palo Alto Cortex XSOAR'
'''


class CortexXSOARPreprocessRule:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.action = module.params['action']
        self.script_id = module.params['script_id']
        self.enabled = module.params['enabled']
        self.propagation_labels = module.params['propagation_labels']
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
        self.id = None
        self.raw_rule = None

    def exists(self):
        url_suffix = 'preprocess/rules'
        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, list):
            return False

        xsoar_rules = [rule for rule in results if rule.get('name') == self.name]

        if not len(xsoar_rules) == 1:
            return False

        xsoar_rule = xsoar_rules[0]

        if not xsoar_rule.get('name') == self.name:
            return False

        # store rule id for uri in delete method
        self.id = xsoar_rule.get('id')

        # store rule json as dict for updating properties in add method
        self.raw_rule = xsoar_rule

        if not xsoar_rule.get('enabled') == self.enabled:
            return False

        if self.propagation_labels:
            if not xsoar_rule.get('propagationLabels') == self.propagation_labels:
                return False

        if self.action:
            if not xsoar_rule.get('action') == self.action:
                return False

        if self.script_id:
            if not xsoar_rule.get('scriptID') == self.script_id:
                return False

        return True

    def add(self):
        url_suffix = 'preprocess/rule'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        if self.raw_rule:
            self.raw_rule['action'] = self.action
            self.raw_rule['scriptID'] = self.script_id
            self.raw_rule['propagationLabels'] = self.propagation_labels or []
            self.raw_rule['enabled'] = self.enabled
            self.raw_rule['version'] = -1

            data = self.raw_rule

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Pre-process rule {self.name} updated in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to update pre-process rule{self.name}", f"Error updating pre-process rule: {str(e)}"
        else:
            data = {
                "propagationLabels": self.propagation_labels or [],
                "name": self.name,
                "newEventFilters": [],
                "existingEventsFilters": [],
                "searchClosed": False,
                "period": {
                    "fromValue": 30,
                    "by": "days"
                },
                "action": self.action,
                "linkTo": "oldest",
                "scriptID": self.script_id,
                "enabled": self.enabled,
                "id": "",
                "shouldPublish": True,
                "shouldCommit": True,
                "commitMessage": "Preprocess rule edited"
            }

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Pre-process rule {self.name} created in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to create pre-process rule{self.name}", f"Error creating pre-process rule: {str(e)}"

    def delete(self):
        url_suffix = f"preprocess/rule/{self.id}"

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        try:
            if not self.module.check_mode:
                open_url(url, method="DELETE", headers=self.headers, validate_certs=self.validate_certs)
            return 0, f"Pre-process rule {self.name} deleted in Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete pre-process rule {self.name}", f"Error deleting pre-process rule: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            propagation_labels=dict(type='list'),
            account=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
            action=dict(type='str', choices=['script']),
            enabled=dict(type='bool', default=True),
            script_id=dict(type='str')
        ),
        supports_check_mode=True,
        required_if=[
            ('action', 'script', ('script_id', 'name'),),
        ],
    )

    client = CortexXSOARPreprocessRule(module)

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
