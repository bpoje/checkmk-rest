import csv
import logging
import sys
import json
from fabric import task
from checkmk import Checkmk, create_checkmk, split_hosts
import checkutil as p


# Author: Blaž Poje
# fabfile <=> frontend
# vse operacije na frontendu so read only, če ni parametra 'doit'


@task(aliases=['h'], help={'get-effective-attributes': 'Fetch effective_attributes for this check mk host'}, autoprint=True)
def get_host(c, hostname, get_effective_attributes=False):
    'check mk: get host'
    return json.dumps(create_checkmk().get_host(hostname, get_effective_attributes).res.json())


@task(aliases=['d'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def delete_host(c, hostname, doit=False):
    'check mk: delete host'
    if doit:
        return create_checkmk().delete_host(hostname)


@task(aliases=['c'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def create_host(c, hostname, folder, ip=None, alias=None, doit=False):
    'check mk: create host'
    if doit:
        return json.dumps(create_checkmk().create_host(hostname, folder, ip, alias).res.json())


@task(aliases=['u'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def update_host(c, hostname, data, etag, doit=False):
    '''check mk: update host
    Change only one parameter: data = {"update_attributes": {"tag_shop": "value1"}}
    Change all checkmk host parameters (any parameters not defined in body will be cleared): data = {"attributes": {"ipaddress": "192.168.0.6"}}
    Remove checkmk parameter (don't change other parameters): data = {"remove_attributes": ["tag_shop_type"]}
    '''
    if doit:
        return json.dumps(create_checkmk().update_host(hostname, data, etag).res.json())


@task(aliases=['ut'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def update_host_tag(c, hostname, tag_group, tag_group_value, doit=False):
    'check mk: update host tag'
    if doit:
        return json.dumps(create_checkmk().update_host_tag(hostname, tag_group, tag_group_value).res.json())


@task(aliases=['rt'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def remove_host_tag(c, hostname, tag_group, doit=False):
    'check mk: remove host tag'
    if doit:
        return json.dumps(create_checkmk().remove_host_tag(hostname, tag_group).res.json())


@task(aliases=['ui'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def update_host_ip(c, hostname, ip, doit=False):
    'check mk: update host ip'
    if doit:
        return json.dumps(create_checkmk().update_host_ipaddress(hostname, ip).res.json())


@task(aliases=['ri'], help={'doit': 'Enable modification (without this flag it is read only)'}, autoprint=True)
def remove_host_ip(c, hostname, doit=False):
    'check mk: remove host ip'
    if doit:
        return json.dumps(create_checkmk().remove_host_ipaddress(hostname).res.json())


@task(aliases=['a'], autoprint=True)
def activate(c, force_foreign_changes=False, doit=False):
    'check mk: activate'
    if doit:
        return json.dumps(create_checkmk().activate_changes(force_foreign_changes).res.json())
    else:
        print(f'doit: {doit}')


@task(aliases=['di'], help={'doit': 'Enable modification (without this flag it is read only)', 'mode': 'mode is one of the enum values: [\'new\', \'remove\', \'fix_all\', \'refresh\', \'only_host_labels\']', 'hostnames': 'hostnames separated with ; or ,'}, autoprint=True)
def discover(c, hostnames, mode, doit=False):
    '''check mk: discover services on check mk hosts'''
    if doit:
        return create_checkmk().discover_services(split_hosts(hostnames), mode)
    else:
        print(f'doit: {doit}')


@task(aliases=['df'], help={'doit': 'Enable modification (without this flag it is read only)', 'hostnames': 'hostnames separated with ; or ,'}, autoprint=True)
def discover_fixall(c, hostnames, doit=False):
    '''check mk: Fix all services on check mk hosts'''
    if doit:
        return create_checkmk().discover_fixall(split_hosts(hostnames))
    else:
        print(f'doit: {doit}')


@task(aliases=['etag'], autoprint=True)
def get_etag(c, hostname):
    'check mk: get etag value (value that changes on every modification of check mk host)'
    return create_checkmk().get_etag(hostname)


@task(aliases=['gtg'], autoprint=True)
def get_tag_group(c, tag_group_name):
    'check mk: Get a host tag group with all its values'
    j = create_checkmk().get_tag_group(tag_group_name).res.json()
    return json.dumps(j)


@task(aliases=['ah'], autoprint=True)
def get_all_hosts(c):
    'check mk: get all hosts in json'
    j = create_checkmk().get_all_hosts().res.json()
    return json.dumps(j)


@task(aliases=['ahf'], autoprint=True)
def get_all_hosts_in_folder(c, folder):
    'check mk: get all hosts in folder'
    j = create_checkmk().get_all_hosts_in_folder(folder).res.json()
    return json.dumps(j)


@task(aliases=['gaf'], autoprint=True)
def get_all_folders(c, parent, recursive=False, show_hosts=False):
    '''check mk: lists subfolders (and the hosts in subfolders) of folder x. It won't show the files that are in folder x. 
    parent string - Show all sub-folders of this folder. The default is the root-folder. Path delimiters can be either ~, / or \. Please use the one most appropriate for your quoting/escaping needs. A good default choice is ~.
    recursive boolean - List the folder (default: root) and all its sub-folders recursively.
    show_hosts boolean - When set, all hosts that are stored in each folder will also be shown. On large setups this may come at a performance cost, so by default this is switched off.
    '''
    j = create_checkmk().get_all_folders(parent, recursive, show_hosts).res.json()
    return json.dumps(j)


@task(aliases=['at'])
def get_all_tags(c):
    'Iterate over all hosts and extract their tags in CSV form'
    res = p.get_all_hosts_tags(create_checkmk())
    print('host;tag_group;value')
    for t in res:
        print(f'{t.host};{t.tag_group};{t.value}')


@task(aliases=['atg'])
def get_all_tag_group(c):
    'Iterate over all tag groups and their possible values (enums) in CSV form'
    res = p.get_all_tag_groups(create_checkmk())
    print('tag_group;tag_group_value;tag_group_value_title')
    for t in res:
        print(f'{t.tag_group};{t.tag_val_id};{t.tag_val_title}')


@task(aliases=['th'])
def get_tag_hist(c):
    'Get all tag groups and their possible values and left join them with hosts that use them. In CSV form'
    res = p.get_tag_histogram(create_checkmk())
    print('tag_group;tag_value;host')
    for key, hosts in res.items():
        tag_group = key[0]
        tag_val_id = key[1]
        for host in hosts:
            print(f'{tag_group};{tag_val_id};{host}')
        if not hosts:
            # Print even if list is empty
            print(f'{tag_group};{tag_val_id};')


@task(aliases=['tes'])
def test(c):
    'test'
    print('test')


def init_logger():
    logging.getLogger('parse-action')
    logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    from invoke import Context
    c = Context()


if 0:
    x = get_all_tag_something(c)
    len(x)
