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
module: xsoar_list
short_description: Create a List in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create a List in Palo Alto Cortex XSOAR
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
    read_roles:
        description: Roles to set Read Only permissions
        required: false
        type: list
    edit_roles:
        description: Roles to set Read and edit permissions
        required: false
        type: list
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
# Create a JSON list from a file in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Create API Key
  cortex.xsoar.xsoar_list:
    name: "Configuration"
    content_type: JSON
    json_content: "{{lookup('ansible.builtin.file', '../files/Configuration.json') |from_json}}"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Create a Text list from a file in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Configuration Text list in account Client01
  cortex.xsoar.xsoar_list:
    name: "Configuration"
    content_type: Text
    content: "{{lookup('ansible.builtin.file', '../files/Configuration.txt')}}"
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    
# Create a Text list with permissions from a file in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Configuration Text list in account Client01
  cortex.xsoar.xsoar_list:
    name: "Configuration"
    content_type: Text
    content: "{{lookup('ansible.builtin.file', '../files/Configuration.txt')}}"
    read_roles: 
      - "Analyst"
    edit_roles:
      - "Administrator"
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"

# Remove a list in Palo Alto Cortex XSOAR
- name: Remove list "List01"
  cortex.xsoar.xsoar_list:
    name: "List01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_list module generates.
    type: str
    returned: on change
    sample: 'List Configuration created in Palo Alto Cortex XSOAR'
'''


class CortexXSOARList:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.content_type = module.params['content_type']
        self.content = module.params['content'] or ""
        self.json_content = module.params['json_content'] or {}
        self.description = module.params['description']
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
        self.read_roles = module.params['read_roles']
        self.edit_roles = module.params['edit_roles']

    def exists(self):
        url_suffix = 'lists'
        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, list):
            return False

        xsoar_lists = [l for l in results if l.get('name') == self.name]

        if not len(xsoar_lists) == 1:
            return False

        xsoar_list = xsoar_lists[0]

        if not xsoar_list.get('id') == self.name:
            return False

        if not xsoar_list.get('type') == self.content_type:
            return False

        if self.description:
            if not xsoar_list.get('description') == self.description:
                return False

        if self.propagation_labels:
            if not xsoar_list.get('propagationLabels') == self.propagation_labels:
                return False

        if self.content:
            if not xsoar_list.get('data') == self.content:
                return False

        if self.json_content:
            if xsoar_list.get('type') == "JSON":
                if not json.loads(xsoar_list.get('data')) == self.json_content:
                    return False

        if not xsoar_list.get('xsoarReadOnlyRoles') == self.read_roles:
            return False

        if not xsoar_list.get('xsoarReadOnlyRoles') == self.edit_roles:
            return False

        return True

    def add(self):
        url_suffix = 'lists/save'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        if self.content_type == "JSON":
            content = json.dumps(self.json_content)
        else:
            content = self.content

        data = {
            "id": self.name,
            "version": -1,
            "propagationLabels": self.propagation_labels,
            "allRead": True,
            "allReadWrite": True,
            "name": self.name,
            "data": content,
            "type": self.content_type,
            "description": self.description
        }

        if self.read_roles:
            data.update({'xsoarReadOnlyRoles': self.read_roles, "allRead": False})
        else:
            data.update({"allRead": True})

        if self.edit_roles:
            data.update({'roles': self.edit_roles, "allReadWrite": False})
        else:
            data.update({"allReadWrite": True})

        json_data = json.dumps(data, ensure_ascii=False)

        try:
            if not self.module.check_mode:
                open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
            return 0, f"List {self.name} created in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to create list {self.name}", f"Error creating list: {str(e)}"

    def delete(self):
        url_suffix = "lists/delete"

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
            return 0, f"List {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete list {self.name}", f"Error deleting list: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            content=dict(type='str'),
            json_content=dict(type='dict'),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            content_type=dict(type='str', choices=['JSON', 'HTML', 'Text', 'Markdown', 'CSS'], default='Text'),
            description=dict(type='str'),
            propagation_labels=dict(type='list', default=["all"]),
            account=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
            read_roles=dict(type='list'),
            edit_roles=dict(type='list')
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('content', 'json_content'),
        ],
        required_if=[
            ('content_type', 'JSON', ('json_content', 'name'), ),
        ],
    )

    client = CortexXSOARList(module)

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
