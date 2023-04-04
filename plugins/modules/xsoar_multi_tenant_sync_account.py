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
module: xsoar_multi_tenant_sync_account
short_description: Synchronize content to accounts in a multi-tenant Palo Alto Cortex XSOAR environment
version_added: "1.1.0"
description: Synchronize content to accounts in a multi-tenant Palo Alto Cortex XSOAR environment
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    url:
        description: URL of Palo Alto Cortex XSOAR.
        required: true
        type: str
    api_key:
        description: API Key to connect to Palo Alto Cortex XSOAR.
        required: true
        type: str
    accounts: 
        description: Accounts to sync content to in a Palo Alto Cortex XSOAR multi-tenant environment.
        required: false
        type: list
    all_accounts:
        description: Sync content to all accounts in a Palo Alto Cortex XSOAR multi-tenant environment.
        required: false
        type: bool
    items: 
        description: Items to sync content to in a Palo Alto Cortex XSOAR multi-tenant environment.
        required: false
        type: list
    all_items:
        description: Sync all content to accounts in a Palo Alto Cortex XSOAR multi-tenant environment.
        required: false
        type: bool
    validate_certs: 
        description:
          - If false, SSL certificates will not be validated.
          - This should only set to false used on personally controlled sites using self-signed certificates.
        required: false
        type: bool
        default: true
    timeout:
        description: The timout in seconds of the Sync All request
        required: false
        type: int
        default: 300

extends_documentation_fragment:
    - cortex.xsoar.xsoar_multi_tenant_sync_account

author:
    - Wouter Stinkens (@wstinkens)
'''

EXAMPLES = r'''
# Synchronize all content to all accounts in a Palo Alto Cortex XSOAR multi-tenant environment with untrusted SSL certificates
- name: Sync all content to all accounts
  cortex.xsoar.xsoar_multi_tenant_sync_account:
    all_items: True
    all_accounts: True
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    validate_certs: False

# Synchronize content to all accounts in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Sync AbuseIPDB content pack to all accounts
  cortex.xsoar.xsoar_multi_tenant_sync_account:
    items:
      - AbuseIPDB
    all_accounts: True
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"

# Synchronize content to an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Sync AbuseIPDB content pack to account
  cortex.xsoar.xsoar_multi_tenant_sync_account:
    items:
      - AbuseIPDB
    accounts:
      - Account01
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
'''

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_multi_tenant_sync_account module generates.
    type: str
    returned: on change
    sample: 'All Accounts synced in Palo Alto Cortex XSOAR'
'''


class CortexXSOARSyncAccount:
    def __init__(self, module):
        self.module = module
        self.base_url = module.params['url']
        self.items = module.params['items']
        self.all_items = module.params['all_items']
        self.api_key = module.params['api_key']
        self.accounts = module.params['accounts']
        self.all_accounts = module.params['all_accounts']
        self.validate_certs = module.params['validate_certs']
        self.headers = {
            "Authorization": f"{self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.timeout = module.params['timeout']

        self.accounts_items_to_sync = {}

    def exists(self):
        if self.all_items is True and self.all_accounts is True:
            return False
        elif self.all_items is True and self.accounts:
            for account in self.accounts:
                account_items_to_sync = self.get_account_items_to_sync(account=account)
                if account_items_to_sync.get('add') and account_items_to_sync.get('override') \
                        and account_items_to_sync.get('remove'):
                    self.accounts_items_to_sync.update({account: account_items_to_sync})
        elif self.all_accounts is True:
            self.accounts = self.get_account_list()

        if self.all_items is not True and self.accounts and isinstance(self.accounts, list) \
                and self.items and isinstance(self.items, list):
            print(f'accounts: {self.accounts}')
            for account in self.accounts:
                account_items_to_sync = self.get_account_items_to_sync(account=account)

                for item in self.items:
                    if (items_to_add := account_items_to_sync.get('add')) and isinstance(items_to_add, dict):
                        for k, v in items_to_add.items():
                            if isinstance(v, list):
                                for item_to_add in v:
                                    if item_to_add.get('name') == item:
                                        self.add_to_accounts_items_to_sync(item=item_to_add, action="add",
                                                                           account=account)
                    if (items_to_override := account_items_to_sync.get('override')) \
                            and isinstance(items_to_override, dict):
                        for k, v in items_to_override.items():
                            if isinstance(v, list):
                                for item_to_override in v:
                                    if item_to_override.get('name') == item:
                                        self.add_to_accounts_items_to_sync(item=item_to_override, action="override",
                                                                           account=account)

        if self.accounts_items_to_sync:
            print(self.accounts_items_to_sync)
            return False

        return True

    def add_to_accounts_items_to_sync(self, item: dict, action: str, account: str):
        item_type = item.get('type')

        if account_to_add := self.accounts_items_to_sync.get(account):
            if action_to_add := account_to_add.get(action):
                if (item_types_to_add := action_to_add.get(item_type)) and isinstance(item_types_to_add, list):
                    item_types_to_add.append(item)
                    self.accounts_items_to_sync[account][action][item_type] = item_types_to_add
                else:
                    action_to_add.update({item_type: [item]})
                    self.accounts_items_to_sync[account][action] = action_to_add
            else:
                account_to_add.update({action: {item_type: [item]}})
                self.accounts_items_to_sync[account] = account_to_add
        else:
            self.accounts_items_to_sync.update({account: {'add': {}, 'override': {}, 'remove': {}}})
            action_to_add = self.accounts_items_to_sync.get(account).get(action)
            action_to_add.update({item_type: [item]})
            self.accounts_items_to_sync[account][action] = action_to_add

    def add(self):
        if self.all_items is True and self.all_accounts is True:
            url_suffix = "accounts/content/sync"

            url = f'{self.base_url}/{url_suffix}'

            data = {}

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data,
                             validate_certs=self.validate_certs,
                             timeout=self.timeout)
                return 0, f"All Accounts synced in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to sync all Accounts", f"Error creating list: {str(e)}"
        else:
            try:
                for k, v in self.accounts_items_to_sync.items():
                    print(f'account: {k}')
                    url_suffix = f"account/content/sync/acc_{k}"

                    url = f'{self.base_url}/{url_suffix}'

                    json_data = json.dumps(v, ensure_ascii=False)
                    print(json_data)

                    if not self.module.check_mode:
                        open_url(url, method="POST", headers=self.headers, data=json_data,
                                 validate_certs=self.validate_certs, timeout=self.timeout)

                return 0, f"Content synced to accounts in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to sync accounts", f"Error syncing account: {str(e)}"

    def get_account_list(self) -> list:
        url_suffix = "accounts"

        url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="GET", headers=self.headers, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, list):
            return []

        return [account.get('displayName') for account in results if isinstance(account, dict)]

    def get_account_items_to_sync(self, account: str) -> dict:
        url_suffix = f"account/content/diff/{account}"

        url = f'{self.base_url}/{url_suffix}'

        response = open_url(url, method="POST", headers=self.headers, data="", validate_certs=self.validate_certs)
        results = json.loads(response.read())

        return results


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            accounts=dict(type='list'),
            all_accounts=dict(type='bool'),
            all_items=dict(type='bool'),
            items=dict(type='list'),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=300)
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ('all_items', 'items'),
            ('all_accounts', 'accounts'),
        ],
    )

    client = CortexXSOARSyncAccount(module)

    rc = None
    msg = ''
    err = ''
    result = {}

    if not client.exists():
        rc, msg, err = client.add()
    if rc is not None and rc != 0:
        module.fail_json(name="Content Sync Failed", msg=err)

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
