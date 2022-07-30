from dataclasses import dataclass
import ipaddress
from operator import attrgetter
import os
import requests
import logging
import json


# business logic


@dataclass
class JsonResult:
    'Result od http request'
    res: requests.Response

    def ok(self):
        return self.res.status_code == 200


def json_result(res: requests.Response) -> JsonResult:
    return JsonResult(res=res)


class Checkmk:
    def __init__(self, url, ca_cert, bearerAuth, site_name):
        self.url = url
        self.ca_cert = ca_cert
        self.username = bearerAuth[0]
        self.secret = bearerAuth[1]
        self.site_name = site_name
        self.session = None

    def open_session(self):
        'Create check MK session'

        # https://docs.checkmk.com/latest/en/rest_api.html
        # The REST-API supports the following methods for authentication: Bearer, Web server and Cookie
        #
        # Bearer or Header authentication:
        # 'Bearer' means the holder of an identity. With HTTP bearer authentication, the client authenticates itself
        # with the access data of a user set up on the Checkmk server. Ideally, this is the so-called automation user,
        # which is provided in Checkmk for the execution of actions via an API. Bearer authentication is recommended for use in scripts.
        #
        # For authentication, you need the user name and the corresponding so-called "automation secret for machine accounts",
        # i.e. the password for the automation user.
        #
        # Both items of information must be transmitted to the Checkmk server in the header of each request.
        #
        # In a newly-created site, the user automation will have already been created. You can find it, like other users,
        # under Setup > Users. Make sure that the roles and associated permissions for the automation user are set to allow you to execute your requests.

        # Create requests session object
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {self.username} {self.secret}',
                                    'accept': 'application/json', 'Content-Type': 'application/json'})

    def log_pre(self, pre):
        'Log prepared requst'
        logging.debug('Prepared request:')
        logging.debug(f'URL: {pre.url}')
        logging.debug(f'BODY: {pre.body}')
        logging.debug(f'HEADERS: {pre.headers}')

    def log_response(self, res):
        'Log response objects'
        # Response objects have a .request property which is the original PreparedRequest object that was sent.
        logging.debug('Response.request:')
        logging.debug(f'res.request.url: {res.request.url}')
        logging.debug(f'res.request.body: {res.request.body}')
        logging.debug(f'res.request.headers: {res.request.headers}')

        # Output response
        logging.debug('Response:')
        logging.debug(f'res.status_code: {res.status_code}')
        logging.debug(f'res: {res}')
        logging.debug(f'res.content: {res.content}')

        # If data not empty
        logging.debug('RESPONSE BODY: ')
        if res.content is not None and len(res.content) != 0:
            # res.content are bytes, decode them to produce string
            dmp = json.loads(res.content.decode('utf-8'))
            # Beautifying JSON output
            logging.debug(json.dumps(dmp, indent=4))
        else:
            logging.debug('No returned data')

        logging.debug(f'RESPONSE HEADERS: {res.headers}')

    def rest_query(self, url_action, req_type='GET', data=None, header=None, send=True):
        'execute rest query'
        if self.session is None:
            raise Exception('Check MK session is not opened')

        req = requests.Request(req_type, self.url + url_action, data=data)
        pre = self.session.prepare_request(req)

        if header is not None:
            pre.headers.update(header)

        self.log_pre(pre)

        if not send:
            return None

        res = self.session.send(pre, verify=self.ca_cert)
        self.log_response(res)
        return json_result(res)

    # POST ​/domain-types​/activation_run​/actions​/activate-changes​/invoke Activate pending changes
    def activate_changes(self, force_foreign_changes=False, send=True):
        'Activate changes on check mk site'
        ffc_str = 'true' if force_foreign_changes else 'false'
        data = {
            'redirect': 'false',
            'sites': [self.site_name],
            'force_foreign_changes': ffc_str}
        data = json.dumps(data)
        url = '/domain-types/activation_run/actions/activate-changes/invoke'
        return self.rest_query(url, req_type='POST', data=data, send=send)

    def discover_services(self, hostnames: list, mode: str, send=True) -> list:
        '''Discover services on check mk hosts
        mode is one of the enum values: ['new', 'remove', 'fix_all', 'refresh', 'only_host_labels']'''
        assert mode in ['new', 'remove', 'fix_all', 'refresh', 'only_host_labels']
        #    raise ValueError("Mode has to be one of values 'new', 'remove', 'fix_all', 'refresh' or 'only_host_labels'")
        data = {'mode': mode}
        data = json.dumps(data)
        res = []
        for host in hostnames:
            print(f'{host} {mode}')
            url = f'/objects/host/{host}/actions/discover_services/invoke'
            res.append(self.rest_query(url, req_type='POST', data=data, send=send))
        return res

    def discover_fixall(self, hostnames: list, send=True) -> list:
        '''Fix all services on check mk hosts'''
        # Execute refresh, execute fix_all, concat lists with result jsons
        return self.discover_services(hostnames, 'refresh', send) + self.discover_services(hostnames, 'fix_all', send)

    def get_host(self, hostname: str, get_effective_attributes: bool, send=True):
        'Get host info'
        eff_str = '?effective_attributes=true' if get_effective_attributes else ''
        url = f'/objects/host_config/{hostname}{eff_str}'
        return self.rest_query(url, req_type='GET', send=send)

    def get_etag(self, hostname: str) -> str:
        'Get host etag (value that changes on every modification of check mk host)'
        json_result = self.get_host(hostname, False)
        if json_result is None:
            # Return empty string so that subsequent REST calls are going to get status 404
            return ''
        else:
            # If hostname was found : get etag value
            return json_result.res.headers['etag']

    # PUT /objects/host_config/{host_name} Update a host
    def update_host_tag(self, hostname: str, tag_group: str, tag_group_value: str, send=True):
        'Update (set new or update existing) tag'
        data = {
            'update_attributes': {
                tag_group: tag_group_value
            }
        }
        data = json.dumps(data)
        etag = self.get_etag(hostname)
        return self.update_host(hostname, data, etag, send)

    def remove_host_tag(self, hostname: str, tag_group: str, send=True):
        'Remove existing tag'
        data = {'remove_attributes': [tag_group, ]}
        data = json.dumps(data)
        etag = self.get_etag(hostname)
        return self.update_host(hostname, data, etag, send)

    def update_host_ipaddress(self, hostname: str, ip: str, send=True):
        'Update (set new or update existing) ipaddress'
        data = {'update_attributes': {'ipaddress': ip}}
        data = json.dumps(data)
        etag = self.get_etag(hostname)
        return self.update_host(hostname, data, etag, send)

    def remove_host_ipaddress(self, hostname: str, send=True):
        'Remove ipaddress (resolve ip from hostname after removal)'
        data = {'remove_attributes': ['ipaddress', ]}
        data = json.dumps(data)
        etag = self.get_etag(hostname)
        return self.update_host(hostname, data, etag, send)

    # PUT /objects/host_config/{host_name} Update a host
    #
    # Examples for function parameter data:
    #   Change checkmk host parameter (don't change other parameters):
    #   {"update_attributes": {"tag_shop": "value1"}}
    #
    #   Change all checkmk host parameters (any parameters not defined in body will be cleared)
    #   {"attributes": {"ipaddress": "192.168.0.6"}}
    #
    #   Remove checkmk parameter (don't change other parameters):
    #   {"remove_attributes": ["tag_shop_type"]}
    def update_host(self, hostname: str, data: str, etag: str, send=True):
        'Update a checkmk host with request body (data) as variable'
        header = {
            'accept': 'application/json',
            'If-Match': etag,
            'Content-Type': 'application/json'
        }
        url = f'/objects/host_config/{hostname}'
        return self.rest_query(url, req_type='PUT', data=data, send=send, header=header)

    def get_tag_group(self, tag_group_name: str, send=True):
        'Get a host tag group with all its values'
        url = f'/objects/host_tag_group/{tag_group_name}'
        return self.rest_query(url, req_type='GET', send=send)

    def get_all_tag_groups(self, send=True):
        'Show all host tag groups'
        url = '/domain-types/host_tag_group/collections/all'
        return self.rest_query(url, req_type='GET', send=send)

    def get_all_hosts(self, send=True):
        'Get all hosts defined in check mk (slow operation)'
        url = '/domain-types/host_config/collections/all'
        return self.rest_query(url, send=send)

    def get_all_hosts_in_folder(self, folder: str, send=True):
        'Get all host in folder: Please replace the path delimiters with the tilde character ~. Path delimiters can be either ~, / or \\'
        url = f'/objects/folder_config/{folder}/collections/hosts'
        return self.rest_query(url, send=send)

    def get_all_folders(self, parent: str, recursive=False, show_hosts=False, send=True):
        '''
        Lists subfolders (and the hosts in subfolders) of folder x. It won't show the files that are in folder x. 
        parent string - Show all sub-folders of this folder. The default is the root-folder. Path delimiters can be either ~, / or \. Please use the one most appropriate for your quoting/escaping needs. A good default choice is ~.
        recursive boolean - List the folder (default: root) and all its sub-folders recursively.
        show_hosts boolean - When set, all hosts that are stored in each folder will also be shown. On large setups this may come at a performance cost, so by default this is switched off.
        '''
        parent_str = f'parent={parent}'
        recursive_str = 'recursive=true' if recursive else 'recursive=false'
        show_hosts_str = 'show_hosts=true' if show_hosts else 'show_hosts=false'
        url = f'/domain-types/folder_config/collections/all?{parent_str}&{recursive_str}&{show_hosts_str}'
        return self.rest_query(url, send=send)

    def delete_host(self, hostname: str, send=True):
        'Delete a checkmk host'
        url = f'/objects/host_config/{hostname}'
        return self.rest_query(url, req_type='DELETE', send=send)

    def create_host(self, hostname, folder, ip=None, alias=None, send=True):
        'Create a checkmk host. If ip is not set, dns is used on hostname.'
        attributes = ({'ipaddress': ip} if ip is not None else {}) | \
            ({'alias': alias} if alias is not None else {})
        data = {'host_name': hostname, 'folder': folder, 'attributes': attributes}
        data = json.dumps(data)
        url = '/domain-types/host_config/collections/all'
        return self.rest_query(url, req_type='POST', data=data, send=send)


def split_hosts(hostnames: str) -> list:
    'Split , or ; separated string to list'
    return hostnames.replace(',', ';').split(';')


def create_checkmk() -> Checkmk:
    'Init checkmk rest API'

    g = os.environ.get

    # Checkmk site name
    site_name = g('SITE_NAME')

    # Checkmk REST URL
    cmk_rest_url = g('REST_URL')

    # CA public certificate
    cafile = g('CAFILE')

    # Checkmk REST username
    username = g('USER')

    # Checkmk filename with secret token
    secret_token_filename = g('TOKENF')

    logging.debug(f'site_name: {site_name}')
    logging.debug(f'cmk_rest_url: {cmk_rest_url}')
    logging.debug(f'cafile: {cafile}')
    logging.debug(f'username: {username}')
    logging.debug(f'secret_token_filename: {secret_token_filename}')

    secret_token = open(secret_token_filename, 'r').readline().strip('\n')

    bearerAuth = [username, secret_token]
    cmk = Checkmk(cmk_rest_url, cafile, bearerAuth, site_name)
    cmk.open_session()

    return cmk
