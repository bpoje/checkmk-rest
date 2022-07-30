import re
from checkmk import Checkmk
from collections import namedtuple

str_tag_reg = re.compile('^tag_', re.UNICODE)

# host has a tag_group set to value
Tag = namedtuple('Tag', 'host tag_group value')

# tag_group can take value tag_value (predefined constants for tag_group)
#TagGroupOption = namedtuple('TagGroupOption', 'tag_group tag_value')
TagGroupOption = namedtuple('TagGroupOption', 'tag_group tag_val_id tag_val_title tag_val_aux_tags')


def is_tag(hostname: str) -> bool:
    'Is string a tag id? (starts with tag_)'
    return str_tag_reg.search(hostname) is not None


def get_all_hosts_tags(cmk: Checkmk) -> list[Tag]:
    'Iterate over all hosts and extract their tags. Returns a list of named tuples Tag.'
    j = cmk.get_all_hosts().res.json()
    res = []

    for host_json in j['value']:
        host_id = host_json['id']

        for key, value in host_json['extensions']['attributes'].items():
            if is_tag(key):
                # print(f'{host_id}: tag detected: key: {key} => value: {value}')
                t = Tag(host_id, key, value)
                res.append(t)
    return res


def get_all_tag_groups(cmk: Checkmk) -> list[TagGroupOption]:
    'Iterate over all tag groups and their possible values (enums). Return a list of named tuples TagGroupOption'
    j = cmk.get_all_tag_groups().res.json()
    tag_groups = []
    for tag_group_json in j['value']:
        tag_group_id = tag_group_json['id']

        # Append 'tag_' if missing (correct CheckMK bug)
        if not is_tag(tag_group_id):
            tag_group_id = 'tag_' + tag_group_id

        for tag_json in tag_group_json['extensions']['tags']:
            tag_val_id = tag_json['id']
            tag_val_title = tag_json['title']
            tag_val_aux_tags = tag_json['aux_tags']
            t = TagGroupOption(tag_group_id, tag_val_id, tag_val_title, tag_val_aux_tags)
            tag_groups.append(t)
    return tag_groups


def get_tag_histogram(cmk: Checkmk) -> list:
    'Get all tag groups and their possible values and use them for dictionary keys. Each key has a list of hosts that use this tag.'
    tag_groups = get_all_tag_groups(cmk)
    host_tags = get_all_hosts_tags(cmk)

    d = {}

    # Use all TagGroupOption for keys in hash table. Init empty list to later store hosts that use that TagGroupOption.
    # d[named tuple TagGroupOption] = []
    for tg in tag_groups:
        key = (tg.tag_group, tg.tag_val_id)
        d[key] = []

    # d[named tuple TagGroupOption] = [ list of hosts that use the tag (that TagGroupOption in key describes) ]
    for ht in host_tags:
        # Host has a tag. Extract it's tag_group and tag_value to create a key (named tuple TagGroupOption).
        key = ht.tag_group, ht.value

        # Use the created key TagGroupOption to find the correct entry in hash table and insert the host to its list
        d[key].append(ht.host)

    return d


def get_tag_group_list(cmk: Checkmk, tag_group_name: str) -> list:
    'Return entire tag group in a list of named tuples TagGroupOption'
    res = cmk.get_tag_group(tag_group_name)

    if not res.ok():
        print(f'Query failed ({res.res.status_code})!')
        return None

    tag_group_id = res.res.json()['id']
    tags_json = res.res.json()['extensions']['tags']
    tags = []
    for tag_json in tags_json:
        t = TagGroupOption(tag_group_id, tag_json['id'], tag_json['title'], tag_json['aux_tags'])
        tags.append(t)

    return tags
