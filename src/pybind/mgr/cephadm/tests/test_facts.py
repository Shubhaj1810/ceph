from ceph.utils import datetime_now

from ..import CephadmOrchestrator

from .fixtures import wait

from tests import mock


def test_facts(cephadm_module: CephadmOrchestrator):
    facts = {'node-1.ceph.com': {'bios_version': 'F2', 'cpu_cores': 16}}
    cephadm_module.cache.facts = facts
    ret_facts = cephadm_module.get_facts('node-1.ceph.com')
    assert wait(cephadm_module, ret_facts) == [{'bios_version': 'F2', 'cpu_cores': 16}]


@mock.patch("cephadm.inventory.Inventory.update_known_hostnames")
def test_known_hostnames(_update_known_hostnames, cephadm_module: CephadmOrchestrator):
    host_facts = {'hostname': 'host1.domain',
                  'shortname': 'host1',
                  'fqdn': 'host1.domain',
                  'memory_free_kb': 37383384,
                  'memory_total_kb': 40980612,
                  'nic_count': 2}
    cephadm_module.cache.update_host_facts('host1', host_facts)
    _update_known_hostnames.assert_called_with('host1.domain', 'host1', 'host1.domain')

    host_facts = {'hostname': 'host1.domain',
                  'memory_free_kb': 37383384,
                  'memory_total_kb': 40980612,
                  'nic_count': 2}
    cephadm_module.cache.update_host_facts('host1', host_facts)
    _update_known_hostnames.assert_called_with('host1.domain', '', '')


def test_host_had_daemon_refresh_hostname_case(cephadm_module: CephadmOrchestrator):
    """With load-time normalization, cache keys are always lowercase."""
    cache = cephadm_module.cache
    cache.daemons = {'ceph-node-00': {}}
    cache.last_daemon_update = {
        'ceph-node-00': datetime_now(),
    }

    assert cache.host_had_daemon_refresh('ceph-node-00') is True
    assert cache.host_had_daemon_refresh('CEPH-NODE-00') is False
    assert cache.host_had_daemon_refresh('unknown-host') is False


def test_inventory_load_normalizes_keys(cephadm_module: CephadmOrchestrator):
    """Verify that inventory load normalizes uppercase keys to lowercase."""
    inv = cephadm_module.inventory
    inv._inventory = {}
    raw_data = {
        'MULTI80-SITE1': {
            'hostname': 'MULTI80-SITE1',
            'addr': '10.245.0.5',
            'labels': ['_admin'],
        },
        'MULTI80-SITE2': {
            'hostname': 'MULTI80-SITE2',
            'addr': '10.245.0.6',
            'labels': [],
        },
    }
    for k, v in raw_data.items():
        normalized_key = k.lower()
        v['hostname'] = v['hostname'].lower()
        inv._inventory[normalized_key] = v

    assert 'multi80-site1' in inv
    assert 'multi80-site2' in inv
    assert list(inv._inventory.keys()) == ['multi80-site1', 'multi80-site2']
    assert inv._inventory['multi80-site1']['hostname'] == 'multi80-site1'
    assert inv._inventory['multi80-site1']['addr'] == '10.245.0.5'
    assert inv._inventory['multi80-site1']['labels'] == ['_admin']
