#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import json
import time

from tempest.lib.cli import base
from tempest.lib.common.utils import data_utils

from manilaclient import config

CONF = config.CONF


class OSCClientTestBase(base.ClientTestBase):
    """Base class for OSC manila functional tests"""

    @classmethod
    def get_admin_client(cls):
        admin_client = base.CLIClient(
            username=CONF.admin_username,
            password=CONF.admin_password,
            tenant_name=CONF.admin_tenant_name,
            uri=CONF.admin_auth_url,
            cli_dir=CONF.manila_exec_dir,
            insecure=CONF.insecure,
            project_domain_name=CONF.admin_project_domain_name or None,
            project_domain_id=CONF.admin_project_domain_id or None,
            user_domain_name=CONF.admin_user_domain_name or None,
            user_domain_id=CONF.admin_user_domain_id or None
        )
        return admin_client

    @classmethod
    def get_user_client(cls):
        user_client = base.CLIClient(
            username=CONF.username,
            password=CONF.password,
            tenant_name=CONF.tenant_name,
            uri=CONF.auth_url,
            cli_dir=CONF.manila_exec_dir,
            insecure=CONF.insecure,
            project_domain_name=CONF.project_domain_name or None,
            project_domain_id=CONF.project_domain_id or None,
            user_domain_name=CONF.user_domain_name or None,
            user_domain_id=CONF.user_domain_id or None
        )
        return user_client

    @property
    def admin_client(self):
        if not hasattr(self, '_admin_client'):
            self._admin_client = self.get_admin_client()
        return self._admin_client

    @property
    def user_client(self):
        if not hasattr(self, '_user_client'):
            self._user_client = self.get_user_client()
        return self._user_client

    def _get_clients(self):
        return self.admin_client

    def _get_property_from_output(self, output):
        """Creates a dictionary from the given output"""
        obj = {}
        items = self.parser.listing(output)
        for item in items:
            obj[item['Field']] = str(item['Value'])
        return obj

    def _wait_for_object_status(self, object_name, object_id, status,
                                timeout=CONF.build_timeout,
                                interval=CONF.build_interval):
        """Waits for a object to reach a given status."""

        start_time = time.time()
        while time.time() - start_time < timeout:
            if status == self.openstack(
                    '%(obj)s show -c status -f value %(id)s'
                    % {'obj': object_name,
                       'id': object_id}).rstrip():
                break
            time.sleep(interval)
        else:
            self.fail("%s %s did not reach status %s after %d seconds."
                      % (object_name, object_id, status, timeout))

    def check_object_deleted(self, object_name, object_id,
                             timeout=CONF.build_timeout,
                             interval=CONF.build_interval):
        """Check that object deleted successfully"""

        cmd = '%s list -c ID -f value' % object_name
        start_time = time.time()
        while time.time() - start_time < timeout:
            if object_id not in self.openstack(cmd):
                break
            time.sleep(interval)
        else:
            self.fail("%s %s not deleted after %d seconds."
                      % (object_name, object_id, timeout))

    def openstack(self, action, flags='', params='', fail_ok=False,
                  merge_stderr=False, client=None):
        """Executes openstack command for given action"""

        if '--os-share-api-version' not in flags:
            flags = (
                flags + '--os-share-api-version %s'
                % CONF.max_api_microversion)

        if client is None:
            client = self.admin_client

        return client.openstack(action, flags=flags, params=params,
                                fail_ok=fail_ok,
                                merge_stderr=merge_stderr)

    def listing_result(self, object_name, command, client=None):
        """Returns output for the given command as list of dictionaries"""

        output = self.openstack(object_name, params=command, client=client)
        result = self.parser.listing(output)
        return result

    def dict_result(self, object_name, command, client=None):
        """Returns output for the given command as dictionary"""

        output = self.openstack(object_name, params=command, client=client)
        result_dict = self._get_property_from_output(output)
        return result_dict

    def create_share(self, share_protocol=None, size=None, name=None,
                     snapshot_id=None, properties=None, share_network=None,
                     description=None, public=False, share_type=None,
                     availability_zone=None, share_group=None,
                     add_cleanup=True, client=None,
                     wait_for_status='available'):

        name = name or data_utils.rand_name('autotest_share_name')
        # share_type = dhss_false until we have implemented
        # share network commands for osc
        share_type = share_type or 'dhss_false'

        cmd = ('create '
               '%(protocol)s %(size)s %(name)s %(desc)s %(public)s %(stype)s'
               % {'protocol': share_protocol or 'NFS',
                  'size': size or '1',
                  'name': '--name %s' % name,
                  'desc': '--description %s' % description,
                  'public': '--public %s' % public,
                  'stype': '--share-type %s' % share_type})

        if snapshot_id:
            cmd = cmd + ' --snapshot-id %s' % snapshot_id
        if properties:
            for key, value in properties.items():
                cmd = (cmd + ' --property %(key)s=%(value)s'
                       % {'key': key, 'value': value})
        if share_network:
            cmd = cmd + ' --share-network %s' % share_network
        if availability_zone:
            cmd = cmd + ' --availability-zone %s' % availability_zone
        if share_group:
            cmd = cmd + ' --share-group %s' % share_group

        share_object = self.dict_result('share', cmd, client=client)
        self._wait_for_object_status(
            'share', share_object['id'], wait_for_status)

        if add_cleanup:
            self.addCleanup(
                self.openstack, 'share delete %s --wait' % share_object['id']
            )
        return share_object

    def list_pools(self, backend=None, host=None, pool=None, detail=False):
        cmd = 'pool list '

        if backend:
            cmd += f'--backend {backend} '
        if pool:
            cmd += f'--pool {pool} '
        if host:
            cmd += f'--host {host} '
        if detail:
            cmd += '--detail'

        pools = self.listing_result('share', cmd)

        return pools

    def create_share_type(self, name=None, dhss=False, description=None,
                          snapshot_support=None,
                          create_share_from_snapshot_support=None,
                          revert_to_snapshot_support=False,
                          mount_snapshot_support=False, extra_specs={},
                          public=True, add_cleanup=True, client=None,
                          formatter=None):

        name = name or data_utils.rand_name('autotest_share_type_name')

        cmd = (f'create {name} {dhss} --public {public}')
        if description:
            cmd += f' --description {description}'
        if snapshot_support:
            cmd += f' --snapshot-support {snapshot_support}'
        if create_share_from_snapshot_support:
            cmd += (' --create-share-from-snapshot-support '
                    f'{create_share_from_snapshot_support}')
        if revert_to_snapshot_support:
            cmd += (' --revert-to-snapshot-support '
                    f' {revert_to_snapshot_support}')
        if mount_snapshot_support:
            cmd += f' --mount-snapshot-support {mount_snapshot_support}'
        if extra_specs:
            specs = ' --extra-specs'
            for key, value in extra_specs.items():
                specs += f' {key}={value}'
            cmd += specs

        if formatter == 'json':
            cmd = f'share type {cmd} -f {formatter} '
            share_type = json.loads(self.openstack(cmd, client=client))
        else:
            share_type = self.dict_result('share type', cmd, client=client)

        if add_cleanup:
            self.addCleanup(
                self.openstack, f'share type delete {share_type["id"]}'
            )
        return share_type

    def list_services(self, host=None, status=None, state=None, zone=None):
        cmd = 'service list '

        if host:
            cmd += f'--host {host} '
        if status:
            cmd += f'--status {status} '
        if state:
            cmd += f'--state {state} '
        if zone:
            cmd += f'--zone {zone} '

        services = self.listing_result('share', cmd)
        return services

    def create_share_access_rule(self, share, access_type,
                                 access_to, properties=None,
                                 access_level=None, wait=False):
        cmd = f'access create {share} {access_type} {access_to} '

        if access_level:
            cmd += f'--access-level {access_level} '
        if properties:
            cmd += f'--properties {properties} '
        if wait:
            cmd += f'--wait'

        access_rule = self.dict_result('share', cmd)

        return access_rule

    def get_share_export_locations(self, share):
        cmd = (f'export location list {share}')
        export_locations = json.loads(self.openstack(f'share {cmd} -f json'))
        return export_locations

    def create_snapshot(self, share, name=None,
                        description=None, wait=None,
                        force=None, add_cleanup=True):

        name = name or data_utils.rand_name('autotest_snapshot_name')

        cmd = (f'snapshot create {share} --name {name} '
               f'--description {description} ')
        if wait:
            cmd += ' --wait'
        if force:
            cmd += ' --force'

        snapshot_object = self.dict_result('share', cmd)
        self._wait_for_object_status(
            'share snapshot', snapshot_object['id'], 'available')

        if add_cleanup:
            self.addCleanup(
                self.openstack,
                f'share snapshot delete {snapshot_object["id"]} --wait')
        return snapshot_object
