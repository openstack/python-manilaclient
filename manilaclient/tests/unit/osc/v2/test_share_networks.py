#   Copyright 2021 Red Hat Inc. All rights reserved.
#
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
#
from unittest import mock
import uuid

import ddt
from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.osc.v2 import share_networks as osc_share_networks
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = ['ID', 'Name']

COLUMNS_DETAIL = [
    'ID',
    'Name',
    'Status',
    'Created At',
    'Updated At',
    'Description',
]


class TestShareNetwork(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareNetwork, self).setUp()
        self.share_networks_mock = self.app.client_manager.share.share_networks
        self.share_networks_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


@ddt.ddt
class TestShareNetworkCreate(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkCreate, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.create.return_value = self.share_network

        self.cmd = osc_share_networks.CreateShareNetwork(self.app, None)

        self.data = self.share_network._info.values()
        self.columns = self.share_network._info.keys()

    @ddt.data('table', 'yaml')
    def test_share_network_create_formatter(self, formatter):
        arglist = [
            '-f', formatter,
        ]
        verifylist = [
            ('formatter', formatter),
        ]
        expected_data = self.share_network._info

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_networks_mock.create.assert_called_once_with(
            name=None,
            description=None,
            neutron_net_id=None,
            neutron_subnet_id=None,
            availability_zone=None)

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(expected_data.values(), data)

    def test_share_network_create_with_args(self):
        fake_neutron_net_id = str(uuid.uuid4())
        fake_neutron_subnet_id = str(uuid.uuid4())
        fake_az = mock.Mock()
        fake_az.name = 'nova'
        fake_az.id = str(uuid.uuid4())

        arglist = [
            '--name', 'zorilla-net',
            '--description', 'fastest-backdoor-network-ever',
            '--neutron-net-id', fake_neutron_net_id,
            '--neutron-subnet-id', fake_neutron_subnet_id,
            '--availability-zone', 'nova',
        ]
        verifylist = [
            ('name', 'zorilla-net'),
            ('description', 'fastest-backdoor-network-ever'),
            ('neutron_net_id', fake_neutron_net_id),
            ('neutron_subnet_id', fake_neutron_subnet_id),
            ('availability_zone', 'nova'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=fake_az):
            columns, data = self.cmd.take_action(parsed_args)

        self.share_networks_mock.create.assert_called_once_with(
            name='zorilla-net',
            description='fastest-backdoor-network-ever',
            neutron_net_id=fake_neutron_net_id,
            neutron_subnet_id=fake_neutron_subnet_id,
            availability_zone='nova',
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


@ddt.ddt
class TestShareNetworkDelete(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkDelete, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())

        self.share_networks_mock.get.return_value = self.share_network

        self.cmd = osc_share_networks.DeleteShareNetwork(self.app, None)

    def test_share_network_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    @ddt.data(True, False)
    def test_share_network_delete_with_wait(self, wait):
        oscutils.wait_for_delete = mock.Mock(return_value=True)
        share_networks = (
            manila_fakes.FakeShareNetwork.create_share_networks(
                count=2))
        arglist = [
            share_networks[0].id,
            share_networks[1].name,
        ]
        if wait:
            arglist.append('--wait')
        verifylist = [
            ('share_network', [share_networks[0].id, share_networks[1].name])
        ]
        if wait:
            verifylist.append(('wait', True))

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        side_effect=share_networks):
            result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.share_networks_mock.delete.call_count,
                         len(share_networks))
        if wait:
            oscutils.wait_for_delete.assert_has_calls([
                mock.call(manager=self.share_networks_mock,
                          res_id=share_networks[0].id),
                mock.call(manager=self.share_networks_mock,
                          res_id=share_networks[1].id)
            ])
        self.assertIsNone(result)

    def test_share_network_delete_exception(self):
        arglist = [
            self.share_network.id,
        ]
        verifylist = [
            ('share_network', [self.share_network.id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_networks_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    def test_share_network_delete_wait_fails(self):
        oscutils.wait_for_delete = mock.Mock(return_value=False)
        arglist = [
            self.share_network.id,
            '--wait',
        ]
        verifylist = [
            ('share_network', [self.share_network.id]),
            ('wait', True),
        ]

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)
        self.share_networks_mock.delete.assert_called_once_with(
            self.share_network)


@ddt.ddt
class TestShareNetworkShow(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkShow, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network
        self.security_services_mock = (
            self.app.client_manager.share.security_services)

        self.cmd = osc_share_networks.ShowShareNetwork(self.app, None)

        self.data = self.share_network._info.values()
        self.columns = self.share_network._info.keys()

    def test_share_network_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    @ddt.data('name', 'id')
    def test_share_network_show_by(self, attr):
        network_to_show = getattr(self.share_network, attr)
        fake_security_service = mock.Mock()
        fake_security_service.id = str(uuid.uuid4())
        fake_security_service.name = 'security-service-%s' % uuid.uuid4().hex
        self.security_services_mock.list = mock.Mock(
            return_value=[fake_security_service])

        arglist = [
            network_to_show,
        ]
        verifylist = [
            ('share_network', network_to_show),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network) as find_resource:

            columns, data = self.cmd.take_action(parsed_args)

            find_resource.assert_called_once_with(
                self.share_networks_mock, network_to_show)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


@ddt.ddt
class TestShareNetworkList(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkList, self).setUp()

        self.share_networks = (
            manila_fakes.FakeShareNetwork.create_share_networks(
                count=2))
        self.share_networks_list = oscutils.sort_items(self.share_networks,
                                                       'name:asc',
                                                       str)

        self.share_networks_mock.list.return_value = self.share_networks_list

        self.values = (oscutils.get_dict_properties(
            s._info, COLUMNS) for s in self.share_networks_list)
        self.expected_search_opts = {
            'all_tenants': False,
            'project_id': None,
            'name': None,
            'created_since': None,
            'created_before': None,
            'neutron_net_id': None,
            'neutron_subnet_id': None,
            'network_type': None,
            'segmentation_id': None,
            'cidr': None,
            'ip_version': None,
            'security_service': None,
            'name~': None,
            'description~': None,
            'description': None,
        }

        self.cmd = osc_share_networks.ListShareNetwork(self.app, None)

    @ddt.data(True, False)
    def test_list_share_networks_with_search_opts(self, with_search_opts):
        if with_search_opts:
            arglist = [
                '--name', 'foo',
                '--ip-version', '4',
                '--description~', 'foo-share-network',
            ]
            verifylist = [
                ('name', 'foo'),
                ('ip_version', '4'),
                ('description~', 'foo-share-network'),
            ]
            self.expected_search_opts.update({
                'name': 'foo',
                'ip_version': '4',
                'description~': 'foo-share-network',
            })
        else:
            arglist = []
            verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_networks_mock.list.assert_called_once_with(
            search_opts=self.expected_search_opts)
        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(self.values), list(data))

    def test_list_share_networks_all_projects(self):
        all_tenants_list = COLUMNS.copy()
        all_tenants_list.append('Project ID')
        self.expected_search_opts.update({'all_tenants': True})
        list_values = (oscutils.get_dict_properties(
            s._info, all_tenants_list) for s in self.share_networks_list)

        arglist = [
            '--all-projects',
        ]

        verifylist = [
            ('all_projects', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_networks_mock.list.assert_called_once_with(
            search_opts=self.expected_search_opts)

        self.assertEqual(all_tenants_list, columns)
        self.assertEqual(list(list_values), list(data))

    def test_list_share_networks_detail(self):
        values = (oscutils.get_dict_properties(
            s._info, COLUMNS_DETAIL) for s in self.share_networks_list)

        arglist = [
            '--detail',
        ]

        verifylist = [
            ('detail', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_networks_mock.list.assert_called_once_with(
            search_opts=self.expected_search_opts)
        self.assertEqual(COLUMNS_DETAIL, columns)
        self.assertEqual(list(values), list(data))

    def test_list_share_networks_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.35")

        arglist = [
            '--description',
            'Description',
        ]
        verifylist = [
            ('description', 'Description'),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


@ddt.ddt
class TestShareNetworkUnset(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkUnset, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())

        self.share_networks_mock.get.return_value = self.share_network
        self.cmd = osc_share_networks.UnsetShareNetwork(self.app, None)

    def test_unset_share_network_name(self):
        arglist = [
            self.share_network.id,
            '--name',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('name', True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            result = self.cmd.take_action(parsed_args)

        self.share_networks_mock.update.assert_called_once_with(
            self.share_network, name='')
        self.assertIsNone(result)

    def test_unset_share_network_description(self):
        arglist = [
            self.share_network.id,
            '--description',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('description', True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.share_networks_mock.update.assert_called_once_with(
            self.share_network, description='')
        self.assertIsNone(result)

    @ddt.data('name', 'security_service')
    def test_unset_share_network_exception_while_updating(self, attr):
        arglist = [
            self.share_network.id,
            '--name',
            '--security-service',
            'fake-security-service',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('name', True),
            ('security_service', 'fake-security-service'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        if attr == 'name':
            self.share_networks_mock.update.side_effect = Exception()
        else:
            self.share_networks_mock.remove_security_service.side_effect = (
                Exception())

        with mock.patch('osc_lib.utils.find_resource',
                        side_effect=[self.share_network,
                                     'fake-security-service']):
            self.assertRaises(exceptions.CommandError,
                              self.cmd.take_action,
                              parsed_args)
        self.share_networks_mock.update.assert_called_once_with(
            self.share_network, name='')
        if attr == 'security_service':
            self.share_networks_mock.remove_security_service\
                .assert_called_once_with(self.share_network,
                                         'fake-security-service')

    def test_unset_share_network_security_service(self):
        arglist = [
            self.share_network.id,
            '--security-service',
            'fake-security-service',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('security_service', 'fake-security-service'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        side_effect=[self.share_network,
                                     'fake-security-service']):
            result = self.cmd.take_action(parsed_args)

        self.assertIsNone(result)
        self.share_networks_mock.remove_security_service\
            .assert_called_once_with(self.share_network,
                                     'fake-security-service')


@ddt.ddt
class TestShareNetworkSet(TestShareNetwork):

    def setUp(self):
        super(TestShareNetworkSet, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())

        self.share_networks_mock.get.return_value = self.share_network

        self.cmd = osc_share_networks.SetShareNetwork(self.app, None)

    @ddt.data({'status': 'error',
               'current_security_service': str(uuid.uuid4()),
               'check_only': True,
               'restart_check': True},
              {'status': None,
               'current_security_service': str(uuid.uuid4()),
               'check_only': True,
               'restart_check': None},
              {'status': None,
               'current_security_service': str(uuid.uuid4()),
               'check_only': True,
               'restart_check': True},
              )
    @ddt.unpack
    def test_set_share_network_api_version_exception(self,
                                                     status,
                                                     current_security_service,
                                                     check_only,
                                                     restart_check):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.62")

        arglist = [self.share_network.id]
        verifylist = [('share_network', self.share_network.id)]
        if status:
            arglist.extend(['--status', status])
            verifylist.append(('status', status))
        if current_security_service:
            arglist.extend(['--current-security-service',
                            current_security_service])
            verifylist.append(('current_security_service',
                               current_security_service))
        if check_only and restart_check:
            arglist.extend(['--check-only', '--restart-check'])
            verifylist.extend([('check_only', True), ('restart_check', True)])

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_set_network_properties(self):
        new_name = 'share-network-name-' + uuid.uuid4().hex
        new_description = 'share-network-description-' + uuid.uuid4().hex
        new_neutron_subnet_id = str(uuid.uuid4())

        arglist = [
            self.share_network.id,
            '--name', new_name,
            '--description', new_description,
            '--neutron-subnet-id', new_neutron_subnet_id,
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('name', new_name),
            ('description', new_description),
            ('neutron_subnet_id', new_neutron_subnet_id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            result = self.cmd.take_action(parsed_args)

        self.share_networks_mock.update.assert_called_once_with(
            self.share_network,
            name=parsed_args.name,
            description=new_description,
            neutron_subnet_id=new_neutron_subnet_id,
        )
        self.assertIsNone(result)

    def test_set_share_network_status(self):
        arglist = [
            self.share_network.id,
            '--status', 'error'
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('status', 'error')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            result = self.cmd.take_action(parsed_args)

        self.share_networks_mock.reset_state.assert_called_once_with(
            self.share_network, parsed_args.status)
        self.assertIsNone(result)

    def test_set_network_update_exception(self):
        share_network_name = 'share-network-name-' + uuid.uuid4().hex
        arglist = [
            self.share_network.id,
            '--name', share_network_name
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('name', share_network_name)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_networks_mock.update.side_effect = Exception()

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            self.assertRaises(exceptions.CommandError,
                              self.cmd.take_action,
                              parsed_args)
        self.share_networks_mock.update.assert_called_once_with(
            self.share_network, name=parsed_args.name)

    def test_set_share_network_status_exception(self):
        arglist = [
            self.share_network.id,
            '--status', 'error'
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('status', 'error')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_networks_mock.reset_state.side_effect = Exception()

        with mock.patch('osc_lib.utils.find_resource',
                        return_value=self.share_network):
            self.assertRaises(exceptions.CommandError,
                              self.cmd.take_action,
                              parsed_args)
        self.share_networks_mock.reset_state.assert_called_once_with(
            self.share_network, parsed_args.status)

    @ddt.data({'check_only': False, 'restart_check': False},
              {'check_only': True, 'restart_check': True},
              {'check_only': True, 'restart_check': False})
    @ddt.unpack
    def test_set_share_network_add_new_security_service_check_reset(
            self, check_only, restart_check):
        self.share_networks_mock .add_security_service_check = mock.Mock(
            return_value=(200, {'compatible': True}))

        arglist = [
            self.share_network.id,
            '--new-security-service', 'new-security-service-name',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('new_security_service', 'new-security-service-name'),
        ]

        if check_only:
            arglist.append('--check-only')
            verifylist.append(('check_only', True))
        if restart_check:
            arglist.append('--restart-check')
            verifylist.append(('restart_check', True))

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        side_effect=[self.share_network,
                                     'new-security-service']):
            result = self.cmd.take_action(parsed_args)

        if check_only:
            self.share_networks_mock.add_security_service_check\
                .assert_called_once_with(self.share_network,
                                         'new-security-service',
                                         reset_operation=restart_check)
            self.share_networks_mock.add_security_service.assert_not_called()
        else:
            self.share_networks_mock.add_security_service_check\
                .assert_not_called()
            self.share_networks_mock.add_security_service\
                .assert_called_once_with(self.share_network,
                                         'new-security-service')
        self.assertIsNone(result)

    @ddt.data({'check_only': False, 'restart_check': False},
              {'check_only': True, 'restart_check': True},
              {'check_only': True, 'restart_check': False})
    @ddt.unpack
    def test_set_share_network_update_security_service_check_reset(
            self, check_only, restart_check):
        self.share_networks_mock\
            .update_share_network_security_service_check = mock.Mock(
                return_value=(200, {'compatible': True}))

        arglist = [
            self.share_network.id,
            '--new-security-service', 'new-security-service-name',
            '--current-security-service', 'current-security-service-name'
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('new_security_service', 'new-security-service-name'),
            ('current_security_service', 'current-security-service-name'),
        ]
        if check_only:
            arglist.append('--check-only')
            verifylist.append(('check_only', True))
        if restart_check:
            arglist.append('--restart-check')
            verifylist.append(('restart_check', True))
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.find_resource',
                        side_effect=[self.share_network,
                                     'new-security-service',
                                     'current-security-service']):
            result = self.cmd.take_action(parsed_args)

        if check_only:
            self.share_networks_mock\
                .update_share_network_security_service_check\
                .assert_called_once_with(self.share_network,
                                         'current-security-service',
                                         'new-security-service',
                                         reset_operation=restart_check)
            self.share_networks_mock.update_share_network_security_service\
                .assert_not_called()
        else:
            self.share_networks_mock\
                .update_share_network_security_service_check\
                .assert_not_called()
            self.share_networks_mock.update_share_network_security_service\
                .assert_called_once_with(self.share_network,
                                         'current-security-service',
                                         'new-security-service')
        self.assertIsNone(result)
