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
                     add_cleanup=True, client=None):

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
            'share', share_object['id'], 'available')

        if add_cleanup:
            self.addCleanup(
                self.openstack, 'share delete %s' % share_object['id']
            )
        return share_object
