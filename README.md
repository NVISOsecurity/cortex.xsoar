# Ansible Collection: cortex.xsoar

The `cortex.xsoar` collection includes Ansible modules to help automate the management of Palo Alto Cortex XSOAR.

This collection has been tested against Palo Alto Cortex XSOAR 6.10.255865.

## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.14.2**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.

## Included content

### Modules
Name | Description
--- | ---
[cortex.xsoar.xsoar_api_key](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_api_key.py#L13)|Create an API Key in Palo Alto Cortex XSOAR
[cortex.xsoar.xsoar_integration](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_integration.py#L13)|Create an integration instance in Palo Alto Cortex XSOAR
[cortex.xsoar.xsoar_job](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_job.py#L15)|Create a job in Palo Alto Cortex XSOAR
[cortex.xsoar.xsoar_list](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_list.py#L13)|Create a list in Palo Alto Cortex XSOAR
[cortex.xsoar.xsoar_preprocess_rule](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_preprocess_rule.py#L13)|Create a preprocess rule in Palo Alto Cortex XSOAR
[cortex.xsoar.xsoar_multi_tenant_account](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_multi_tenant_account.py#L13)|Create an account in a multi-tenant Palo Alto Cortex XSOAR environment
[cortex.xsoar.xsoar_multi_tenant_sync_accounts](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_multi_tenant_sync_accounts.py#L13)|Synchronize content to all accounts in a multi-tenant Palo Alto Cortex XSOAR environment
[cortex.xsoar.xsoar_multi_tenant_sync_account](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_multi_tenant_sync_account.py#L13)|Synchronize content to accounts in a multi-tenant Palo Alto Cortex XSOAR environment
[cortex.xsoar.xsoar_credential](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/plugins/modules/xsoar_credential.py#L13)|Create a Credential in Palo Alto Cortex XSOAR

## Installing this collection

You can install the Palo Alto Cortex XSOAR collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install git@github.com:NVISOsecurity/cortex.xsoar.git

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: https://github.com/NVISOsecurity/cortex.xsoar.git
    type: git
```

## Using this collection

### Using modules from the Cortex XSOAR collection in your playbooks

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `cortex.xsoar.xsoar_integration`.
The following example task creates an integration instance of Demisto REST API on Palo Alto Cortex XSOAR, using the FQCN:

```yaml
---
- name: Create Demisto REST API integration instance
  cortex.xsoar.xsoar_integration:
    name: "Demisto REST API_instance"
    brand: "Demisto REST API"
    enabled: True
    configuration:
        url: "https://127.0.0.1"
        insecure: True
        apikey: "71F9CAC0D57544C7C7DFB78BE50FC96A"
        proxy: True
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    validate_certs: False
```

## Release notes

Release notes are available [here](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/CHANGELOG.rst).

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.