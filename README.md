# Ansible Collection: cortex.xsoar

The `cortex.xsoar` collection includes Ansible modules to help automate the management of Palo Alto Cortex XSOAR.

This collection has been tested against Palo Alto Cortex XSOAR 6.9.

## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.14.2**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.

## Included content

### Modules
Name | Description
--- | ---
cortex.xsoar.xsoar_api_key|Create an API Key in Palo Alto Cortex XSOAR
cortex.xsoar.xsoar_integration|Create an integration instance in Palo Alto Cortex XSOAR
cortex.xsoar.xsoar_job|Create a job in Palo Alto Cortex XSOAR
cortex.xsoar.xsoar_preprocess_rule|Create a preprocess rule in Palo Alto Cortex XSOAR
cortex.xsoar.xsoar_multi_tenant_account|Create an account in a multi-tenant Palo Alto Cortex XSOAR environment
cortex.xsoar.xsoar_multi_tenant_sync_accounts|Synchronize content to all accounts in a multi-tenant Palo Alto Cortex XSOAR environment

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

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `cortex.xsoar.xsoar_api_key`.
The following example task creates an API key on Palo Alto Cortex XSOAR, using the FQCN:

```yaml
---
- name: Create an API Key
  cortex.xsoar.xsoar_api_key:
    name: "API Key 1"
    state: "present"
    url: "https://xsoar.org"
    api_key: "47A424BF668FD7BF0443184314104BC3"
    key: "71F9CAC0D57544C7C7DFB78BE50FC96A"
```

## Release notes

Release notes are available [here](https://github.com/NVISOsecurity/cortex.xsoar/blob/main/CHANGELOG.rst).

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.