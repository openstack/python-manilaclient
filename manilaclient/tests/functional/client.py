# Copyright 2014 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re
import time

from oslo_utils import strutils
import six
from tempest.lib.cli import base
from tempest.lib.cli import output_parser
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as tempest_lib_exc

from manilaclient import config
from manilaclient.tests.functional import exceptions
from manilaclient.tests.functional import utils

CONF = config.CONF
SHARE = 'share'
SHARE_TYPE = 'share_type'
SHARE_NETWORK = 'share_network'


def not_found_wrapper(f):

    def wrapped_func(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except tempest_lib_exc.CommandFailed as e:
            if re.search('No (\w+) with a name or ID', e.stderr):
                # Raise appropriate 'NotFound' error
                raise tempest_lib_exc.NotFound()
            raise

    return wrapped_func


def forbidden_wrapper(f):

    def wrapped_func(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except tempest_lib_exc.CommandFailed as e:
            if re.search('HTTP 403', e.stderr):
                # Raise appropriate 'Forbidden' error.
                raise tempest_lib_exc.Forbidden()
            raise

    return wrapped_func


class ManilaCLIClient(base.CLIClient):

    def __init__(self, *args, **kwargs):
        super(ManilaCLIClient, self).__init__(*args, **kwargs)
        if CONF.enable_protocols:
            self.share_protocol = CONF.enable_protocols[0]
        else:
            msg = "Configuration option 'enable_protocols' is not defined."
            raise exceptions.InvalidConfiguration(reason=msg)
        self.build_interval = CONF.build_interval
        self.build_timeout = CONF.build_timeout

    def manila(self, action, flags='', params='', fail_ok=False,
               endpoint_type='publicURL', merge_stderr=False,
               microversion=None):
        """Executes manila command for the given action.

        :param action: the cli command to run using manila
        :type action: string
        :param flags: any optional cli flags to use. For specifying
                      microversion, please, use 'microversion' param
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param fail_ok: if True an exception is not raised when the
                        cli return code is non-zero
        :type fail_ok: boolean
        :param endpoint_type: the type of endpoint for the service
        :type endpoint_type: string
        :param merge_stderr: if True the stderr buffer is merged into stdout
        :type merge_stderr: boolean
        :param microversion: API microversion to be used for request
        :type microversion: str
        """
        flags += ' --endpoint-type %s' % endpoint_type
        if not microversion:
            # NOTE(vponomaryov): use max API version from config
            microversion = CONF.max_api_microversion

        # NOTE(vponomaryov): it is possible that param 'flags' already
        # can contain '--os-share-api-version' key. If it is so and we
        # reached this part then value of 'microversion' param will be
        # used and existing one in 'flags' param will be ignored.
        flags += ' --os-share-api-version %s' % microversion
        return self.cmd_with_auth(
            'manila', action, flags, params, fail_ok, merge_stderr)

    def wait_for_resource_deletion(self, res_type, res_id, interval=3,
                                   timeout=180, microversion=None):
        """Resource deletion waiter.

        :param res_type: text -- type of resource. Supported only 'share_type'.
            Other types support is TODO.
        :param res_id: text -- ID of resource to use for deletion check
        :param interval: int -- interval between requests in seconds
        :param timeout: int -- total time in seconds to wait for deletion
        """
        # TODO(vponomaryov): add support for other resource types
        if res_type == SHARE_TYPE:
            func = self.is_share_type_deleted
        elif res_type == SHARE_NETWORK:
            func = self.is_share_network_deleted
        elif res_type == SHARE:
            func = self.is_share_deleted
        else:
            raise exceptions.InvalidResource(message=res_type)

        end_loop_time = time.time() + timeout
        deleted = func(res_id, microversion=microversion)

        while not (deleted or time.time() > end_loop_time):
            time.sleep(interval)
            deleted = func(res_id, microversion=microversion)

        if not deleted:
            raise exceptions.ResourceReleaseFailed(
                res_type=res_type, res_id=res_id)

    # Share types

    def create_share_type(self, name=None, driver_handles_share_servers=True,
                          snapshot_support=True, is_public=True,
                          microversion=None):
        """Creates share type.

        :param name: text -- name of share type to use, if not set then
            autogenerated will be used
        :param driver_handles_share_servers: bool/str -- boolean or its
            string alias. Default is True.
        :param snapshot_support: bool/str -- boolean or its
            string alias. Default is True.
        :param is_public: bool/str -- boolean or its string alias. Default is
            True.
        """
        if name is None:
            name = data_utils.rand_name('manilaclient_functional_test')
        dhss = driver_handles_share_servers
        if not isinstance(dhss, six.string_types):
            dhss = six.text_type(dhss)
        if not isinstance(snapshot_support, six.string_types):
            snapshot_support = six.text_type(snapshot_support)
        if not isinstance(is_public, six.string_types):
            is_public = six.text_type(is_public)
        cmd = ('type-create %(name)s %(dhss)s --is-public %(is_public)s '
               '--snapshot-support %(snapshot_support)s') % {
                   'name': name, 'dhss': dhss, 'is_public': is_public,
                   'snapshot_support': snapshot_support}
        share_type_raw = self.manila(cmd, microversion=microversion)
        share_type = output_parser.details(share_type_raw)
        return share_type

    @not_found_wrapper
    def delete_share_type(self, share_type, microversion=None):
        """Deletes share type by its Name or ID."""
        return self.manila(
            'type-delete %s' % share_type, microversion=microversion)

    def list_share_types(self, list_all=True, columns=None, microversion=None):
        """List share types.

        :param list_all: bool -- whether to list all share types or only public
        :param columns: comma separated string of columns.
            Example, "--columns id,name"
        """
        cmd = 'type-list'
        if list_all:
            cmd += ' --all'
        if columns is not None:
            cmd += ' --columns ' + columns
        share_types_raw = self.manila(cmd, microversion=microversion)
        share_types = output_parser.listing(share_types_raw)
        return share_types

    def get_share_type(self, share_type, microversion=None):
        """Get share type.

        :param share_type: str -- Name or ID of share type
        """
        share_types = self.list_share_types(True, microversion=microversion)
        for st in share_types:
            if share_type in (st['ID'], st['Name']):
                return st
        raise tempest_lib_exc.NotFound()

    def is_share_type_deleted(self, share_type, microversion=None):
        """Says whether share type is deleted or not.

        :param share_type: text -- Name or ID of share type
        """
        # NOTE(vponomaryov): we use 'list' operation because there is no
        # 'get/show' operation for share-types available for CLI
        share_types = self.list_share_types(
            list_all=True, microversion=microversion)
        for list_element in share_types:
            if share_type in (list_element['ID'], list_element['Name']):
                return False
        return True

    def wait_for_share_type_deletion(self, share_type, microversion=None):
        """Wait for share type deletion by its Name or ID.

        :param share_type: text -- Name or ID of share type
        """
        self.wait_for_resource_deletion(
            SHARE_TYPE, res_id=share_type, interval=2, timeout=6,
            microversion=microversion)

    def get_project_id(self, name_or_id):
        try:
            # Temporary workaround for bug #1497162
            project_id = self.openstack(
                'project show -f value -c id %s' % name_or_id)
        except Exception:
            tenant = self.keystone("tenant-get %s" % name_or_id)
            project_id = re.search("id(.*)\|(.*)\|", tenant).group(2).strip()
        return project_id.strip()

    @not_found_wrapper
    def add_share_type_access(self, share_type_name_or_id, project_id,
                              microversion=None):
        data = dict(st=share_type_name_or_id, project=project_id)
        self.manila('type-access-add %(st)s %(project)s' % data,
                    microversion=microversion)

    @not_found_wrapper
    def remove_share_type_access(self, share_type_name_or_id, project_id,
                                 microversion=None):
        data = dict(st=share_type_name_or_id, project=project_id)
        self.manila('type-access-remove %(st)s %(project)s' % data,
                    microversion=microversion)

    @not_found_wrapper
    def list_share_type_access(self, share_type_id, microversion=None):
        projects_raw = self.manila(
            'type-access-list %s' % share_type_id, microversion=microversion)
        projects = output_parser.listing(projects_raw)
        project_ids = [pr['Project_ID'] for pr in projects]
        return project_ids

    @not_found_wrapper
    def set_share_type_extra_specs(self, share_type_name_or_id, extra_specs,
                                   microversion=None):
        """Set key-value pair for share type."""
        if not (isinstance(extra_specs, dict) and extra_specs):
            raise exceptions.InvalidData(
                message='Provided invalid extra specs - %s' % extra_specs)
        cmd = 'type-key %s set ' % share_type_name_or_id
        for key, value in extra_specs.items():
            cmd += '%(key)s=%(value)s ' % {'key': key, 'value': value}
        return self.manila(cmd, microversion=microversion)

    @not_found_wrapper
    def unset_share_type_extra_specs(self, share_type_name_or_id,
                                     extra_specs_keys, microversion=None):
        """Unset key-value pair for share type."""
        if not (isinstance(extra_specs_keys, (list, tuple, set)) and
                extra_specs_keys):
            raise exceptions.InvalidData(
                message='Provided invalid extra specs - %s' % extra_specs_keys)
        cmd = 'type-key %s unset ' % share_type_name_or_id
        for key in extra_specs_keys:
            cmd += '%s ' % key
        return self.manila(cmd, microversion=microversion)

    def list_all_share_type_extra_specs(self, microversion=None):
        """List extra specs for all share types."""
        extra_specs_raw = self.manila(
            'extra-specs-list', microversion=microversion)
        extra_specs = utils.listing(extra_specs_raw)
        return extra_specs

    def list_share_type_extra_specs(self, share_type_name_or_id,
                                    microversion=None):
        """List extra specs for specific share type by its Name or ID."""
        all_share_types = self.list_all_share_type_extra_specs(
            microversion=microversion)
        for share_type in all_share_types:
            if share_type_name_or_id in (share_type['ID'], share_type['Name']):
                return share_type['all_extra_specs']
        raise exceptions.ShareTypeNotFound(share_type=share_type_name_or_id)

    # Share networks

    def create_share_network(self, name=None, description=None,
                             nova_net_id=None, neutron_net_id=None,
                             neutron_subnet_id=None, microversion=None):
        """Creates share network.

        :param name: text -- desired name of new share network
        :param description: text -- desired description of new share network
        :param nova_net_id: text -- ID of Nova network
        :param neutron_net_id: text -- ID of Neutron network
        :param neutron_subnet_id: text -- ID of Neutron subnet

        NOTE: 'nova_net_id' and 'neutron_net_id'/'neutron_subnet_id' are
            mutually exclusive.
        """
        params = self._combine_share_network_data(
            name=name,
            description=description,
            nova_net_id=nova_net_id,
            neutron_net_id=neutron_net_id,
            neutron_subnet_id=neutron_subnet_id)
        share_network_raw = self.manila(
            'share-network-create %s' % params, microversion=microversion)
        share_network = output_parser.details(share_network_raw)
        return share_network

    def _combine_share_network_data(self, name=None, description=None,
                                    nova_net_id=None, neutron_net_id=None,
                                    neutron_subnet_id=None):
        """Combines params for share network operations 'create' and 'update'.

        :returns: text -- set of CLI parameters
        """
        data = dict()
        if name is not None:
            data['--name'] = name
        if description is not None:
            data['--description'] = description
        if nova_net_id is not None:
            data['--nova_net_id'] = nova_net_id
        if neutron_net_id is not None:
            data['--neutron_net_id'] = neutron_net_id
        if neutron_subnet_id is not None:
            data['--neutron_subnet_id'] = neutron_subnet_id
        cmd = ''
        for key, value in data.items():
            cmd += "%(k)s=%(v)s " % dict(k=key, v=value)
        return cmd

    @not_found_wrapper
    def get_share_network(self, share_network, microversion=None):
        """Returns share network by its Name or ID."""
        share_network_raw = self.manila(
            'share-network-show %s' % share_network, microversion=microversion)
        share_network = output_parser.details(share_network_raw)
        return share_network

    @not_found_wrapper
    def update_share_network(self, share_network, name=None, description=None,
                             nova_net_id=None, neutron_net_id=None,
                             neutron_subnet_id=None, microversion=None):
        """Updates share-network by its name or ID.

        :param name: text -- new name for share network
        :param description: text -- new description for share network
        :param nova_net_id: text -- ID of some Nova network
        :param neutron_net_id: text -- ID of some Neutron network
        :param neutron_subnet_id: text -- ID of some Neutron subnet

        NOTE: 'nova_net_id' and 'neutron_net_id'/'neutron_subnet_id' are
            mutually exclusive.
        """
        sn_params = self._combine_share_network_data(
            name=name,
            description=description,
            nova_net_id=nova_net_id,
            neutron_net_id=neutron_net_id,
            neutron_subnet_id=neutron_subnet_id)
        share_network_raw = self.manila(
            'share-network-update %(sn)s %(params)s' % dict(
                sn=share_network, params=sn_params),
            microversion=microversion)
        share_network = output_parser.details(share_network_raw)
        return share_network

    @not_found_wrapper
    def delete_share_network(self, share_network, microversion=None):
        """Deletes share network by its Name or ID."""
        return self.manila('share-network-delete %s' % share_network,
                           microversion=microversion)

    @staticmethod
    def _stranslate_to_cli_optional_param(param):
        if len(param) < 1 or not isinstance(param, six.string_types):
            raise exceptions.InvalidData(
                'Provided wrong parameter for translation.')
        while not param[0:2] == '--':
            param = '-' + param
        return param.replace('_', '-')

    def list_share_networks(self, all_tenants=False, filters=None,
                            columns=None, microversion=None):
        """List share networks.

        :param all_tenants: bool -- whether to list share-networks that belong
            only to current project or for all projects.
        :param filters: dict -- filters for listing of share networks.
            Example, input:
                {'project_id': 'foo'}
                {'-project_id': 'foo'}
                {'--project_id': 'foo'}
                {'project-id': 'foo'}
            will be transformed to filter parameter "--project-id=foo"
         :param columns: comma separated string of columns.
            Example, "--columns id"
        """
        cmd = 'share-network-list '
        if columns is not None:
            cmd += ' --columns ' + columns
        if all_tenants:
            cmd += ' --all-tenants '
        if filters and isinstance(filters, dict):
            for k, v in filters.items():
                cmd += '%(k)s=%(v)s ' % {
                    'k': self._stranslate_to_cli_optional_param(k), 'v': v}
        share_networks_raw = self.manila(cmd, microversion=microversion)
        share_networks = utils.listing(share_networks_raw)
        return share_networks

    def is_share_network_deleted(self, share_network, microversion=None):
        """Says whether share network is deleted or not.

        :param share_network: text -- Name or ID of share network
        """
        share_types = self.list_share_networks(True, microversion=microversion)
        for list_element in share_types:
            if share_network in (list_element['id'], list_element['name']):
                return False
        return True

    def wait_for_share_network_deletion(self, share_network,
                                        microversion=None):
        """Wait for share network deletion by its Name or ID.

        :param share_network: text -- Name or ID of share network
        """
        self.wait_for_resource_deletion(
            SHARE_NETWORK, res_id=share_network, interval=2, timeout=6,
            microversion=microversion)

    # Shares

    def create_share(self, share_protocol, size, share_network=None,
                     share_type=None, name=None, description=None,
                     public=False, snapshot=None, metadata=None,
                     microversion=None):
        """Creates a share.

        :param share_protocol: str -- share protocol of a share.
        :param size: int/str -- desired size of a share.
        :param share_network: str -- Name or ID of share network to use.
        :param share_type: str -- Name or ID of share type to use.
        :param name: str -- desired name of new share.
        :param description: str -- desired description of new share.
        :param public: bool -- should a share be public or not.
            Default is False.
        :param snapshot: str -- Name or ID of a snapshot to use as source.
        :param metadata: dict -- key-value data to provide with share creation.
        :param microversion: str -- API microversion that should be used.
        """
        cmd = 'create %(share_protocol)s %(size)s ' % {
            'share_protocol': share_protocol, 'size': size}
        if share_network is not None:
            cmd += '--share-network %s ' % share_network
        if share_type is not None:
            cmd += '--share-type %s ' % share_type
        if name is None:
            name = data_utils.rand_name('autotest_share_name')
        cmd += '--name %s ' % name
        if description is None:
            description = data_utils.rand_name('autotest_share_description')
        cmd += '--description %s ' % description
        if public:
            cmd += '--public'
        if snapshot is not None:
            cmd += '--snapshot %s ' % snapshot
        if metadata:
            metadata_cli = ''
            for k, v in metadata.items():
                metadata_cli += '%(k)s=%(v)s ' % {'k': k, 'v': v}
            if metadata_cli:
                cmd += '--metadata %s ' % metadata_cli
        share_raw = self.manila(cmd, microversion=microversion)
        share = output_parser.details(share_raw)
        return share

    @not_found_wrapper
    def get_share(self, share, microversion=None):
        """Returns a share by its Name or ID."""
        share_raw = self.manila('show %s' % share, microversion=microversion)
        share = output_parser.details(share_raw)
        return share

    @not_found_wrapper
    def update_share(self, share, name=None, description=None,
                     is_public=False, microversion=None):
        """Updates a share.

        :param share: str -- name or ID of a share that should be updated.
        :param name: str -- desired name of new share.
        :param description: str -- desired description of new share.
        :param is_public: bool -- should a share be public or not.
            Default is False.
        """
        cmd = 'update %s ' % share
        if name:
            cmd += '--name %s ' % name
        if description:
            cmd += '--description %s ' % description
        is_public = strutils.bool_from_string(is_public, strict=True)
        cmd += '--is-public %s ' % is_public

        return self.manila(cmd, microversion=microversion)

    @not_found_wrapper
    @forbidden_wrapper
    def delete_share(self, shares, microversion=None):
        """Deletes share[s] by Names or IDs.

        :param shares: either str or list of str that can be either Name
            or ID of a share(s) that should be deleted.
        """
        if not isinstance(shares, list):
            shares = [shares]
        cmd = 'delete '
        for share in shares:
            cmd += '%s ' % share
        return self.manila(cmd, microversion=microversion)

    def list_shares(self, all_tenants=False, filters=None, columns=None,
                    microversion=None):
        """List shares.

        :param all_tenants: bool -- whether to list shares that belong
            only to current project or for all projects.
        :param filters: dict -- filters for listing of shares.
            Example, input:
                {'project_id': 'foo'}
                {-'project_id': 'foo'}
                {--'project_id': 'foo'}
                {'project-id': 'foo'}
            will be transformed to filter parameter "--project-id=foo"
        :param columns: comma separated string of columns.
            Example, "--columns Name,Size"
        """
        cmd = 'list '
        if all_tenants:
            cmd += '--all-tenants '
        if filters and isinstance(filters, dict):
            for k, v in filters.items():
                cmd += '%(k)s=%(v)s ' % {
                    'k': self._stranslate_to_cli_optional_param(k), 'v': v}
        if columns is not None:
            cmd += '--columns ' + columns
        shares_raw = self.manila(cmd, microversion=microversion)
        shares = utils.listing(shares_raw)
        return shares

    def list_share_instances(self, share_id=None, microversion=None):
        """List share instances.

        :param share_id: ID of a share to filter by.
        :param microversion: API microversion to be used for request.
        """
        cmd = 'share-instance-list '
        if share_id:
            cmd += '--share-id %s' % share_id
        share_instances_raw = self.manila(cmd, microversion=microversion)
        share_instances = utils.listing(share_instances_raw)
        return share_instances

    def is_share_deleted(self, share, microversion=None):
        """Says whether share is deleted or not.

        :param share: str -- Name or ID of share
        """
        try:
            self.get_share(share, microversion=microversion)
            return False
        except tempest_lib_exc.NotFound:
            return True

    def wait_for_share_deletion(self, share, microversion=None):
        """Wait for share deletion by its Name or ID.

        :param share: str -- Name or ID of share
        """
        self.wait_for_resource_deletion(
            SHARE, res_id=share, interval=5, timeout=300,
            microversion=microversion)

    def wait_for_share_status(self, share, status, microversion=None):
        """Waits for a share to reach a given status."""
        body = self.get_share(share, microversion=microversion)
        share_name = body['name']
        share_status = body['status']
        start = int(time.time())

        while share_status != status:
            time.sleep(self.build_interval)
            body = self.get_share(share, microversion=microversion)
            share_status = body['status']

            if share_status == status:
                return
            elif 'error' in share_status.lower():
                raise exceptions.ShareBuildErrorException(share=share)

            if int(time.time()) - start >= self.build_timeout:
                message = (
                    "Share %(share_name)s failed to reach %(status)s status "
                    "within the required time (%(build_timeout)s s)." % {
                        "share_name": share_name, "status": status,
                        "build_timeout": self.build_timeout})
                raise tempest_lib_exc.TimeoutException(message)

    @not_found_wrapper
    def _set_share_metadata(self, share, data, update_all=False,
                            microversion=None):
        """Sets a share metadata.

        :param share: str -- Name or ID of a share.
        :param data: dict -- key-value pairs to set as metadata.
        :param update_all: bool -- if set True then all keys except provided
            will be deleted.
        """
        if not (isinstance(data, dict) and data):
            msg = ('Provided invalid data for setting of share metadata - '
                   '%s' % data)
            raise exceptions.InvalidData(message=msg)
        if update_all:
            cmd = 'metadata-update-all %s ' % share
        else:
            cmd = 'metadata %s set ' % share
        for k, v in data.items():
            cmd += '%(k)s=%(v)s ' % {'k': k, 'v': v}
        return self.manila(cmd, microversion=microversion)

    def update_all_share_metadata(self, share, data, microversion=None):
        metadata_raw = self._set_share_metadata(
            share, data, True, microversion=microversion)
        metadata = output_parser.details(metadata_raw)
        return metadata

    def set_share_metadata(self, share, data, microversion=None):
        return self._set_share_metadata(
            share, data, False, microversion=microversion)

    @not_found_wrapper
    def unset_share_metadata(self, share, keys, microversion=None):
        """Unsets some share metadata by keys.

        :param share: str -- Name or ID of a share
        :param keys: str/list -- key or list of keys to unset.
        """
        if not (isinstance(keys, list) and keys):
            msg = ('Provided invalid data for unsetting of share metadata - '
                   '%s' % keys)
            raise exceptions.InvalidData(message=msg)
        cmd = 'metadata %s unset ' % share
        for key in keys:
            cmd += '%s ' % key
        return self.manila(cmd, microversion=microversion)

    @not_found_wrapper
    def get_share_metadata(self, share, microversion=None):
        """Returns list of all share metadata.

        :param share: str -- Name or ID of a share.
        """
        metadata_raw = self.manila(
            'metadata-show %s' % share, microversion=microversion)
        metadata = output_parser.details(metadata_raw)
        return metadata

    @not_found_wrapper
    def list_access(self, share_id, columns=None, microversion=None):
        """Returns list of access rules for a share.

        :param share_id: str -- Name or ID of a share.
        :param columns: comma separated string of columns.
            Example, "--columns access_type,access_to"
        """
        cmd = 'access-list %s ' % share_id
        if columns is not None:
            cmd += ' --columns ' + columns
        access_list_raw = self.manila(cmd, microversion=microversion)
        return output_parser.listing(access_list_raw)

    @not_found_wrapper
    def get_access(self, share_id, access_id, microversion=None):
        for access in self.list_access(share_id, microversion=microversion):
            if access['id'] == access_id:
                return access
        raise tempest_lib_exc.NotFound()

    @not_found_wrapper
    def access_allow(self, share_id, access_type, access_to, access_level,
                     microversion=None):
        raw_access = self.manila(
            'access-allow  --access-level %(level)s %(id)s %(type)s '
            '%(access_to)s' % {
                'level': access_level,
                'id': share_id,
                'type': access_type,
                'access_to': access_to,
            },
            microversion=microversion)
        return output_parser.details(raw_access)

    @not_found_wrapper
    def access_deny(self, share_id, access_id, microversion=None):
        return self.manila(
            'access-deny %(share_id)s %(access_id)s' % {
                'share_id': share_id,
                'access_id': access_id,
            },
            microversion=microversion)

    def wait_for_access_rule_status(self, share_id, access_id, state='active',
                                    microversion=None):
        access = self.get_access(
            share_id, access_id, microversion=microversion)

        start = int(time.time())
        while access['state'] != state:
            time.sleep(self.build_interval)
            access = self.get_access(
                share_id, access_id, microversion=microversion)

            if access['state'] == state:
                return
            elif access['state'] == 'error':
                raise exceptions.AccessRuleCreateErrorException(
                    access=access_id)

            if int(time.time()) - start >= self.build_timeout:
                message = (
                    "Access rule %(access)s failed to reach %(state)s state "
                    "within the required time (%(build_timeout)s s)." % {
                        "access": access_id, "state": state,
                        "build_timeout": self.build_timeout})
                raise tempest_lib_exc.TimeoutException(message)

    def wait_for_access_rule_deletion(self, share_id, access_id,
                                      microversion=None):
        try:
            access = self.get_access(
                share_id, access_id, microversion=microversion)
        except tempest_lib_exc.NotFound:
            return

        start = int(time.time())
        while True:
            time.sleep(self.build_interval)
            try:
                access = self.get_access(
                    share_id, access_id, microversion=microversion)
            except tempest_lib_exc.NotFound:
                return

            if access['state'] == 'error':
                raise exceptions.AccessRuleDeleteErrorException(
                    access=access_id)

            if int(time.time()) - start >= self.build_timeout:
                message = (
                    "Access rule %(access)s failed to reach deleted state "
                    "within the required time (%s s)." % self.build_timeout)
                raise tempest_lib_exc.TimeoutException(message)

    def create_security_service(self, type='ldap', name=None, description=None,
                                dns_ip=None, server=None, domain=None,
                                user=None, password=None, microversion=None):
        """Creates security service.

        :param type: security service type (ldap, kerberos or active_directory)
        :param name: desired name of new security service.
        :param description: desired description of new security service.
        :param dns_ip: DNS IP address inside tenant's network.
        :param server: security service IP address or hostname.
        :param domain: security service domain.
        :param user: user of the new security service.
        :param password: password used by user.
        """

        cmd = 'security-service-create %s ' % type
        cmd += self. _combine_security_service_data(
            name=name,
            description=description,
            dns_ip=dns_ip,
            server=server,
            domain=domain,
            user=user,
            password=password)

        ss_raw = self.manila(cmd, microversion=microversion)
        security_service = output_parser.details(ss_raw)
        return security_service

    @not_found_wrapper
    def update_security_service(self, security_service, name=None,
                                description=None, dns_ip=None, server=None,
                                domain=None, user=None, password=None,
                                microversion=None):
        cmd = 'security-service-update %s ' % security_service
        cmd += self. _combine_security_service_data(
            name=name,
            description=description,
            dns_ip=dns_ip,
            server=server,
            domain=domain,
            user=user,
            password=password)
        return output_parser.details(
            self.manila(cmd, microversion=microversion))

    def _combine_security_service_data(self, name=None, description=None,
                                       dns_ip=None, server=None, domain=None,
                                       user=None, password=None):
        data = ''
        if name is not None:
            data += '--name %s ' % name
        if description is not None:
            data += '--description %s ' % description
        if dns_ip is not None:
            data += '--dns-ip %s ' % dns_ip
        if server is not None:
            data += '--server %s ' % server
        if domain is not None:
            data += '--domain %s ' % domain
        if user is not None:
            data += '--user %s ' % user
        if password is not None:
            data += '--password %s ' % password
        return data

    @not_found_wrapper
    def list_share_export_locations(self, share, columns=None,
                                    microversion=None):
        """List share export locations.

        :param share: str -- Name or ID of a share.
        :param columns: str -- comma separated string of columns.
            Example, "--columns uuid,path".
        :param microversion: API microversion to be used for request.
        """
        cmd = "share-export-location-list %s" % share
        if columns is not None:
            cmd += " --columns " + columns
        export_locations_raw = self.manila(cmd, microversion=microversion)
        export_locations = utils.listing(export_locations_raw)
        return export_locations

    @not_found_wrapper
    def get_share_export_location(self, share, export_location_uuid,
                                  microversion=None):
        """Returns an export location by share and its UUID.

        :param share: str -- Name or ID of a share.
        :param export_location_uuid: str -- UUID of an export location.
        :param microversion: API microversion to be used for request.
        """
        share_raw = self.manila(
            'share-export-location-show %(share)s %(el_uuid)s' % {
                'share': share,
                'el_uuid': export_location_uuid,
            },
            microversion=microversion)
        share = output_parser.details(share_raw)
        return share

    @not_found_wrapper
    @forbidden_wrapper
    def list_share_instance_export_locations(self, share_instance,
                                             columns=None, microversion=None):
        """List share instance export locations.

        :param share_instance: str -- Name or ID of a share instance.
        :param columns: str -- comma separated string of columns.
            Example, "--columns uuid,path".
        :param microversion: API microversion to be used for request.
        """
        cmd = "share-instance-export-location-list %s" % share_instance
        if columns is not None:
            cmd += " --columns " + columns
        export_locations_raw = self.manila(cmd, microversion=microversion)
        export_locations = utils.listing(export_locations_raw)
        return export_locations

    @not_found_wrapper
    @forbidden_wrapper
    def get_share_instance_export_location(self, share_instance,
                                           export_location_uuid,
                                           microversion=None):
        """Returns an export location by share instance and its UUID.

        :param share_instance: str -- Name or ID of a share instance.
        :param export_location_uuid: str -- UUID of an export location.
        :param microversion: API microversion to be used for request.
        """
        share_raw = self.manila(
            'share-instance-export-location-show '
            '%(share_instance)s %(el_uuid)s' % {
                'share_instance': share_instance,
                'el_uuid': export_location_uuid,
            },
            microversion=microversion)
        share = output_parser.details(share_raw)
        return share
