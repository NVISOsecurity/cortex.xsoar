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
module: xsoar_api_integration
short_description: Create an integration instance in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create an integration instance in Palo Alto Cortex XSOAR
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
  - Editing integration parameters of type 9 is not support once the integration instance has been created
options:
    name:
        description: Name of the API Key.
        required: true
        type: str
    brand:
        description: Source Brand of integration instance to configure
        required: true
        type: str
    enabled:
        description: Is the integration instance enabled
        required: false
        type: bool
        default: true
    default_ignore:
        description: Is Do not use by default checkbox enabled
        required: false
        type: bool
        default: false
    configuration:
        description: Key/Value pairs of configuration options of the integration instance
        required: true
        type: dict
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
    - cortex.xsoar.xsoar_integration

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Create an integration instance of the Demisto REST API integration in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Create Demisto REST API integration instance
  cortex.xsoar.xsoar_integration:
    name: "Demisto REST API_instance"
    brand: "Demisto REST API"
    enabled: True
    configuration:
        url: "https://127.0.0.1/acc_client01"
        insecure: True
        apikey: "71F9CAC0D57544C7C7DFB78BE50FC96A"
        proxy: True
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    validate_certs: False

# Create an integration instance of the Demisto REST API integration in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Demisto REST API integration instance in account client01
  cortex.xsoar.xsoar_integration:
    name: "Demisto REST API_instance"
    brand: "Demisto REST API"
    enabled: True
    configuration:
        url: "https://127.0.0.1/acc_client01"
        insecure: True
        apikey: "71F9CAC0D57544C7C7DFB78BE50FC96A"
        proxy: True
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    validate_certs: False
    account: "client01"

# Remove an integration instance of the Demisto REST API integration in Palo Alto Cortex XSOAR
- name: Remove integration instance 
  cortex.xsoar.xsoar_integration:
    name: "Demisto REST API_instance"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_integration module generates.
    type: str
    returned: on change
    sample: 'Integration instance Demisto REST API_instance_1 updated in Palo Alto Cortex XSOAR'
'''


class CortexXSOARIntegration:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.brand = module.params['brand']
        self.enabled = module.params['enabled']
        self.configuration = module.params['configuration']
        self.default_ignore = module.params['default_ignore']
        self.propagation_labels = module.params['propagation_labels'] or []
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
        self.raw_instance = None
        self.incomingMapperId = module.params['incomingMapperId']

    def exists(self):
        url_suffix = 'settings/integration/search'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        data = {
            "size": 500
        }

        json_data = json.dumps(data, ensure_ascii=False)

        response = open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, dict):
            return False

        if not (instances := results.get('instances')) or not isinstance(instances, list):
            return False

        xsoar_integration_instances = [i for i in instances if i.get('name') == self.name]

        if not len(xsoar_integration_instances) == 1:
            return False

        xsoar_integration_instance = xsoar_integration_instances[0]

        self.raw_instance = xsoar_integration_instance

        self.id = xsoar_integration_instance.get('id')

        if not xsoar_integration_instance.get('defaultIgnore') == self.default_ignore:
            return False

        if not xsoar_integration_instance.get('brand') == self.brand:
            return False
        
        if not xsoar_integration_instance.get('incomingMapperId') == self.incomingMapperId:
            return False

        for k, v in self.configuration.items():
            if not (config_items := [c for c in xsoar_integration_instance.get('data') if c.get('name') == k]) \
                    or not len(config_items) == 1:
                return False

            if not config_items[0].get('type') == 4 and not config_items[0].get('type') == 9:
                if not config_items[0].get('value') == v:
                    return False

        return True

    def add(self):
        url_suffix = 'settings/integration'

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        if self.raw_instance:

            configuration = self.raw_instance['data']

            for i, config_item in enumerate(self.raw_instance['data']):
                for k, v in self.configuration.items():
                    if config_item.get('name') == k and config_item.get('type') != 9:
                        configuration[i]['value'] = v

            self.raw_instance['version'] = -1
            self.raw_instance['defaultIgnore'] = self.default_ignore or self.raw_instance['defaultIgnore']
            self.raw_instance['enabled'] = str(self.enabled).lower()
            self.raw_instance['data'] = configuration
            self.raw_instance['incomingMapperId'] = self.incomingMapperId

            data = self.raw_instance

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="PUT", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Integration instance {self.name} updated in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to update integration instance {self.name}", f"Error updating integration instance: {str(e)}"

        else:
            configuration = []

            for k, v in self.configuration.items():
                if isinstance(v, dict) and v.get('password'):
                    configuration.append({'name': k, 'value': v, 'type': 9})
                else:
                    configuration.append({'name': k, 'value': v})

            data = {
                "name": self.name,
                "enabled": str(self.enabled).lower(),
                "data": configuration,
                "brand": self.brand,
                "version": 0,
                "isIntegrationScript": True,
                "defaultIgnore": self.default_ignore,
                "incomingMapperId": self.incomingMapperId
            }

            if self.propagation_labels:
                data.update({"propagationLabels": self.propagation_labels})

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="PUT", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Integration instance {self.name} created in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to create integration instance {self.name}", f"Error creating integration instance: {str(e)}"

    def delete(self):
        url_suffix = f"settings/integration/{self.id}"

        if self.account:
            url = f'{self.base_url}/acc_{self.account}/{url_suffix}'
        else:
            url = f'{self.base_url}/{url_suffix}'

        try:
            if not self.module.check_mode:
                open_url(url, method="DELETE", headers=self.headers, validate_certs=self.validate_certs)
            return 0, f"Integration instance {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete integration instance {self.name}", f"Error deleting integration instance: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            brand=dict(type='str', required=True),
            configuration=dict(type='dict', required=True),
            enabled=dict(type='bool', default=True),
            default_ignore=dict(type='bool', default=False),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            propagation_labels=dict(type='list'),
            account=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
            incomingMapperId=dict(type='str', required=False),
        ),
        supports_check_mode=True
    )

    client = CortexXSOARIntegration(module)

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
