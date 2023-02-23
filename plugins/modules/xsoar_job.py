#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

import json
from datetime import datetime, timezone
from dateutil.parser import parse
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

__metaclass__ = type

DOCUMENTATION = r'''
---
module: xsoar_job
short_description: Create a Job in Palo Alto Cortex XSOAR
version_added: "1.0.0"
description: Create a Job in Palo Alto Cortex XSOAR
notes:
  - Tested against Palo Alto Cortex XSOAR 6.10 (B187344).
options:
    name:
        description: Name of the Job.
        required: true
        type: str
    cron:
        description: cron schedule of the Job.
        required: true
        type: str
    playbook_id:
        description: ID of the playbook to execute.
        required: true
        type: str
    active:
        description: Is the Job enabled.
        required: false
        type: bool
        default: True
    incident_type:
        description: The type of the Job incident.
        required: false
        type: str
        default: 'Unclassified'
    owner:
        description: The owner of the Job incident.
        required: false
        type: str
    ending_type:
        description: The ending type of the Job.
        required: false
        type: str
        default: never
    start_date:
        description: The start date of the Job in ISO format.
        required: false
        type: str
        default: now
    end_date:
        description: The end date of the Job in ISO format.
        required: false
        type: str
    close_previous_run:
        description: If a previous job instance is active when a new instance is triggered, cancel the previous job instance and trigger a new job instance.
        required: false
        type: bool
        default: False
    should_trigger_new:
        description: If a previous job instance is active when a new instance is triggered, trigger a new job instance and run concurrently with the previous instance.
        required: false
        type: bool
        default: False
    notify_owner:
        description: If a previous job instance is active when a new instance is triggered, notify the owner.
        required: false
        type: bool
        default: False
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
# Create a Job in Palo Alto Cortex XSOAR with untrusted SSL certificates
- name: Create Job
  cortex.xsoar.xsoar_job:
    name: "Job01"
    cron: "1 * * * *"
    playbook_id: "b22ce079-8f65-4238-84c3-64c6e1a90f5e"
    owner: "Administrator"
    start_date: "now"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
    validate_certs: False

# Create a Job in an account in a Palo Alto Cortex XSOAR multi-tenant environment
- name: Create Job in account Client01
  cortex.xsoar.xsoar_job:
    name: "Job01"
    cron: "*/30 * * * *"
    playbook_id: "b22ce079-8f65-4238-84c3-64c6e1a90f5e"
    owner: "Administrator"
    start_date: "now"
    account: "Client01"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"

# Remove a Job in Palo Alto Cortex XSOAR
- name: Remove Job "Job01"
  cortex.xsoar.xsoar_job:
    name: "Job01"
    state: "absent"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the xsoar_job module generates.
    type: str
    returned: on change
    sample: 'Job Job01 created in Palo Alto Cortex XSOAR'
'''


class CortexXSOARJob:
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.cron = module.params['cron']
        self.owner = module.params['owner']
        self.playbook_id = module.params['playbook_id']
        self.close_previous_run = module.params['close_previous_run']
        self.should_trigger_new = module.params['should_trigger_new']
        self.notify_owner = module.params['notify_owner']
        self.active = module.params['active']
        self.start_date = module.params['start_date']
        self.end_date = module.params['end_date']
        self.ending_type = module.params['ending_type']
        self.incident_type = module.params['incident_type']
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
        self.raw_job = None
        if self.start_date == "now":
            self.start_date = datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            self.start_date = parse(self.start_date).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if self.ending_type == "never":
            self.end_date = self.start_date
        elif self.end_date:
            self.end_date = parse(self.end_date).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def exists(self):
        url_suffix = 'jobs/search'

        url = f'{self.base_url}/acc_{self.account}/{url_suffix}'

        data = {"page": 0, "size": 500, "query": "", "sort": [{"field": "id", "asc": False}]}

        json_data = json.dumps(data, ensure_ascii=False)

        response = open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
        results = json.loads(response.read())

        if not results or not isinstance(results, dict):
            return False

        if not (result_data := results.get('data')) or not isinstance(result_data, list):
            return False

        xsoar_jobs = [job for job in result_data if job.get('name') == self.name]

        if not len(xsoar_jobs) == 1:
            return False

        xsoar_job = xsoar_jobs[0]

        if not xsoar_job.get('name') == self.name:
            return False

        # store job id for uri in delete method
        self.id = xsoar_job.get('id')

        # store job json as dict for updating properties in add method
        self.raw_job = xsoar_job

        if self.cron:
            if not xsoar_job.get('cron') == self.cron:
                return False

        if self.owner:
            if not xsoar_job.get('owner') == self.owner:
                return False

        if self.playbook_id:
            if not xsoar_job.get('playbookId') == self.playbook_id:
                return False

        if self.close_previous_run is not None:
            if not xsoar_job.get('closePrevRun') == self.close_previous_run:
                return False

        if self.should_trigger_new is not None:
            if not xsoar_job.get('shouldTriggerNew') == self.should_trigger_new:
                return False

        if self.notify_owner is not None:
            if not xsoar_job.get('notifyOwner') == self.notify_owner:
                return False

        if self.active is not None:
            if not xsoar_job.get('CustomFields', {}).get('isactive') == str(self.active).lower():
                return False

        if self.incident_type:
            if not xsoar_job.get('type') == self.incident_type:
                return False

        return True

    def add(self):
        url_suffix = 'jobs'

        url = f'{self.base_url}/acc_{self.account}/{url_suffix}'

        if self.raw_job:

            self.raw_job['version'] = -1
            if self.active is not None:
                self.raw_job['CustomFields']['isactive'] = str(self.active)
            self.raw_job['type'] = self.incident_type or self.raw_job['type']
            self.raw_job['rawType'] = self.incident_type or self.raw_job['rawType']
            self.raw_job['name'] = self.name or self.raw_job['name']
            self.raw_job['rawName'] = self.name or self.raw_job['rawName']
            self.raw_job['playbookId'] = self.playbook_id or self.raw_job['playbookId']
            self.raw_job['type'] = self.incident_type or self.raw_job['type']
            self.raw_job['rawType'] = self.incident_type or self.raw_job['rawType']
            self.raw_job['cron'] = self.cron or self.raw_job['cron']
            self.raw_job['shouldTriggerNew'] = self.should_trigger_new or self.raw_job['shouldTriggerNew']
            self.raw_job['closePrevRun'] = self.close_previous_run or self.raw_job['closePrevRun']
            self.raw_job['notifyOwner'] = self.notify_owner or self.raw_job['notifyOwner']
            self.raw_job['owner'] = self.owner or self.raw_job['owner']
            self.raw_job['endingType'] = self.ending_type or self.raw_job['endingType']
            self.raw_job['startDate'] = self.start_date or self.raw_job['startDate']
            self.raw_job['endingDate'] = self.end_date or self.raw_job['endingDate']

            data = self.raw_job

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Job {self.name} updated in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to update job {self.name}", f"Error updating job: {str(e)}"

        else:
            data = {
                "owner": self.owner,
                "type": self.incident_type,
                "playbookId": self.playbook_id,
                "CustomFields": {
                    "isactive": str(self.active).lower()
                },
                "scheduled": True,
                "recurrent": True,
                "startDate": self.start_date,
                "endingDate": self.end_date,
                "endingType": self.ending_type,
                "times": 0,
                "cron": self.cron,
                "cronView": True,
                "humanCron": {},
                "tags": [],
                "isFeed": False,
                "selectedFeeds": [],
                "name": self.name,
                "runOnce": False,
                "valid": True,
                "schedulerEmpty": False,
                "timezoneOffset": -60,
                "timezone": "Europe/Brussels",
                "isDateSelectionOpen": False,
                "isStartDateSelectionOpen": False,
                "endingMomentOb": self.end_date,
                "startMomentOb": self.start_date,
                "atTimeHour": "",
                "atTimeMinute": "",
                "isAllFeeds": False,
                "shouldTriggerNew": self.should_trigger_new,
                "closePrevRun": self.close_previous_run,
                "notifyOwner": self.notify_owner
            }

            json_data = json.dumps(data, ensure_ascii=False)

            try:
                if not self.module.check_mode:
                    open_url(url, method="POST", headers=self.headers, data=json_data, validate_certs=self.validate_certs)
                return 0, f"Job {self.name} created in Palo Alto Cortex XSOAR", ""
            except Exception as e:
                return 1, f"Failed to create job {self.name}", f"Error creating job: {str(e)}"

    def delete(self):
        url_suffix = f'jobs/{self.id}'

        url = f'{self.base_url}/acc_{self.account}/{url_suffix}'

        try:
            if not self.module.check_mode:
                open_url(url, method="DELETE", headers=self.headers, validate_certs=self.validate_certs)
            return 0, f"Job {self.name} deleted in Palo Alto Cortex XSOAR", ""
        except Exception as e:
            return 1, f"Failed to delete job {self.name}", f"Error deleting job: {str(e)}"


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            url=dict(type='str', required=True),
            api_key=dict(type='str', required=True),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
            account=dict(type='str', required=True),
            validate_certs=dict(type='bool', default=True),
            cron=dict(type='str', required=True),
            playbook_id=dict(type=str, required=True),
            close_previous_run=dict(type='bool', default=False),
            should_trigger_new=dict(type='bool', default=False),
            notify_owner=dict(type='bool', default=False),
            owner=dict(type='str'),
            active=dict(type='bool', default=True),
            start_date=dict(type='str', default='now'),
            end_date=dict(type='str'),
            ending_type=dict(type='str', default="never"),
            incident_type=dict(type='str', default="Unclassified")
        ),
        supports_check_mode=True
    )

    client = CortexXSOARJob(module)

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
