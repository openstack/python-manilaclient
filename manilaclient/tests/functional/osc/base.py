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
                     add_cleanup=True, client=None, wait=None,
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
        if wait:
            cmd = cmd + ' --wait'

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
                                 access_level=None, wait=False,
                                 lock_visibility=False,
                                 lock_deletion=False,
                                 lock_reason=None,
                                 add_cleanup=False):
        cmd = f'access create {share} {access_type} {access_to} '

        if access_level:
            cmd += f'--access-level {access_level} '
        if properties:
            cmd += f'--properties {properties} '
        if wait:
            cmd += '--wait '
        if lock_visibility:
            cmd += '--lock-visibility '
        if lock_deletion:
            cmd += '--lock-deletion '
        if lock_reason:
            cmd += f'--lock-reason {lock_reason}'

        access_rule = self.dict_result('share', cmd)

        return access_rule

    def get_share_export_locations(self, share):
        cmd = (f'export location list {share}')
        export_locations = json.loads(self.openstack(f'share {cmd} -f json'))
        return export_locations

    def create_snapshot(self, share, name=None,
                        description=None, wait=True, force=None,
                        add_cleanup=True, client=None):

        name = name or data_utils.rand_name('autotest_snapshot_name')

        cmd = (f'snapshot create {share} --name {name} ')

        if description:
            cmd += f' --description {description}'
        if wait:
            cmd += ' --wait'
        if force:
            cmd += ' --force'

        snapshot_object = self.dict_result('share', cmd, client=client)

        if add_cleanup:
            self.addCleanup(
                self.openstack,
                f'share snapshot delete {snapshot_object["id"]} --wait')

        return snapshot_object

    def create_share_transfer(self, share, name=None, client=None):

        name = name or data_utils.rand_name('autotest_share_transfer_name')
        cmd = (f'transfer create {share} --name {name} ')
        transfer_object = self.dict_result('share', cmd, client=client)

        return transfer_object

    def create_share_network(self, neutron_net_id=None,
                             neutron_subnet_id=None, name=None,
                             description=None, availability_zone=None,
                             add_cleanup=True):
        name = name or data_utils.rand_name('autotest_share_network_name')
        cmd = (f'network create --name {name} --description {description}')
        if neutron_net_id:
            cmd = cmd + f' --neutron-net-id {neutron_net_id}'
        if neutron_subnet_id:
            cmd = cmd + f' --neutron-subnet-id {neutron_subnet_id}'
        if availability_zone:
            cmd = cmd + f' --availability-zone {availability_zone}'

        share_network_obj = self.dict_result('share', cmd)
        self._wait_for_object_status(
            'share network', share_network_obj['id'], 'active')
        if add_cleanup:
            self.addCleanup(
                self.openstack,
                f'share network delete {share_network_obj["id"]}'
            )
        return share_network_obj

    def create_share_replica(self, share, availability_zone=None,
                             share_network=None, wait=None,
                             add_cleanup=True):
        cmd = (f'replica create {share}')

        if availability_zone:
            cmd = cmd + f' --availability-zone {availability_zone}'
        if wait:
            cmd = cmd + ' --wait'
        if share_network:
            cmd = cmd + ' --share-network %s' % share_network

        replica_object = self.dict_result('share', cmd)
        self._wait_for_object_status(
            'share replica', replica_object['id'], 'available')

        if add_cleanup:
            self.addCleanup(
                self.openstack,
                f'share replica delete {replica_object["id"]} --wait'
            )
        return replica_object

    def get_share_replica_export_locations(self, replica):
        cmd = (f'replica export location list {replica}')
        export_locations = self.listing_result('share', cmd)
        return export_locations

    def create_share_group_type(self, name=None, share_types=None,
                                group_specs=None, public=True,
                                add_cleanup=True):

        name = name or data_utils.rand_name('autotest_share_group_types_name')
        share_types = share_types or 'None'

        cmd = (f'group type create '
               f'{name} '
               f'{share_types} ')

        if group_specs:
            cmd = cmd + f' --group-specs {group_specs} '
        if not public:
            cmd = cmd + f' --public {public} '

        share_object = self.dict_result('share', cmd)

        if add_cleanup:
            self.addCleanup(
                self.openstack,
                'share group type delete %s' % share_object['id'])
        return share_object

    def share_group_type_access_create(self, group_type, project):
        cmd = (f'group type access create '
               f'{group_type} '
               f'{project} ')

        self.dict_result('share', cmd)

    def share_group_type_access_delete(self, group_type, access_id):
        cmd = (f'group type access delete '
               f'{group_type} '
               f'{access_id} ')

        self.dict_result('share', cmd)

    def check_create_network_subnet(self, share_network, neutron_net_id=None,
                                    neutron_subnet_id=None,
                                    availability_zone=None,
                                    restart_check=None):
        cmd = f'network subnet create {share_network} --check-only'

        if neutron_net_id:
            cmd += f' --neutron-net-id {neutron_net_id}'
        if neutron_subnet_id:
            cmd += f' --neutron-subnet-id {neutron_subnet_id}'
        if availability_zone:
            cmd += f' --availability-zone {availability_zone}'
        if restart_check:
            cmd += ' --restart-check'

        check_result = self.dict_result('share', cmd)
        return check_result

    def create_resource_lock(self, resource_id, resource_type='share',
                             resource_action='delete', lock_reason=None,
                             add_cleanup=True, client=None):

        cmd = f'lock create {resource_id} {resource_type}'
        cmd += f' --resource-action {resource_action}'

        if lock_reason:
            cmd += f' --reason "{lock_reason}"'

        lock = self.dict_result('share', cmd, client=client)

        if add_cleanup:
            self.addCleanup(self.openstack,
                            'share lock delete %s' % lock['id'],
                            client=client)
        return lock

    def create_backup(self, share_id, name=None, description=None,
                      backup_options=None, add_cleanup=True):

        name = name or data_utils.rand_name('autotest_backup_name')

        cmd = (f'backup create {share_id} ')

        if name:
            cmd += f' --name {name}'
        if description:
            cmd += f' --description {description}'
        if backup_options:
            options = ' --backup-options'
            for key, value in backup_options.items():
                options += f' {key}={value}'
            cmd += options

        backup_object = self.dict_result('share', cmd)
        self._wait_for_object_status(
            'share backup', backup_object['id'], 'available')

        if add_cleanup:
            self.addCleanup(
                self.openstack,
                f'share backup delete {backup_object["id"]} --wait')

        return backup_object
