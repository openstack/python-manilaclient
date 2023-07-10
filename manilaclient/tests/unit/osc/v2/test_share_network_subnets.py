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

from manilaclient import api_versions
from manilaclient.osc.v2 import share_network_subnets as osc_share_subnets
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareNetworkSubnet(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareNetworkSubnet, self).setUp()

        self.share_networks_mock = self.app.client_manager.share.share_networks
        self.share_networks_mock.reset_mock()

        self.share_subnets_mock = (
            self.app.client_manager.share.share_network_subnets)
        self.share_subnets_mock.reset_mock()


@ddt.ddt
class TestShareNetworkSubnetCreate(TestShareNetworkSubnet):

    def setUp(self):
        super(TestShareNetworkSubnetCreate, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network

        self.share_network_subnet = (
            manila_fakes.FakeShareNetworkSubnet.create_one_share_subnet())
        self.share_subnets_mock.create.return_value = self.share_network_subnet

        self.cmd = osc_share_subnets.CreateShareNetworkSubnet(
            self.app, None)

        self.data = self.share_network_subnet._info.values()
        self.columns = self.share_network_subnet._info.keys()

    def test_share_network_subnet_create_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_network_subnet_create(self):
        fake_neutron_net_id = str(uuid.uuid4())
        fake_neutron_subnet_id = str(uuid.uuid4())

        arglist = [
            self.share_network.id,
            '--neutron-net-id', fake_neutron_net_id,
            '--neutron-subnet-id', fake_neutron_subnet_id,
            '--availability-zone', 'nova',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('neutron_net_id', fake_neutron_net_id),
            ('neutron_subnet_id', fake_neutron_subnet_id),
            ('availability_zone', 'nova'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_subnets_mock.create.assert_called_once_with(
            neutron_net_id=fake_neutron_net_id,
            neutron_subnet_id=fake_neutron_subnet_id,
            availability_zone='nova',
            share_network_id=self.share_network.id,
            metadata={}
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)

    def test_share_network_subnet_create_arg_group_exception(self):
        fake_neutron_net_id = str(uuid.uuid4())

        arglist = [
            self.share_network.id,
            '--neutron-net-id', fake_neutron_net_id
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('neutron_net_id', fake_neutron_net_id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)

    @ddt.data({'check_only': False, 'restart_check': True},
              {'check_only': True, 'restart_check': True},
              {'check_only': True, 'restart_check': False})
    @ddt.unpack
    def test_share_network_subnet_create_check_api_version_exception(
            self, check_only, restart_check):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.69'
        )
        arglist = [
            self.share_network.id,
        ]
        verifylist = [
            ('share_network', self.share_network.id),
        ]
        if check_only:
            arglist.append('--check-only')
            verifylist.append(('check_only', True))
        if restart_check:
            arglist.append('--restart-check')
            verifylist.append(('restart_check', True))
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    @ddt.data(True, False)
    def test_share_network_subnet_create_check(self, restart_check):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.70'
        )
        self.share_networks_mock.share_network_subnet_create_check = (
            mock.Mock(return_value=(200, {'compatible': True})))
        arglist = [
            self.share_network.id,
            '--check-only'
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('check_only', True),
        ]
        if restart_check:
            arglist.append('--restart-check')
            verifylist.append(('restart_check', True))
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        (self.share_networks_mock.share_network_subnet_create_check
         .assert_called_once_with(
             share_network_id=self.share_network.id, neutron_net_id=None,
             neutron_subnet_id=None, availability_zone=None,
             reset_operation=restart_check))

    def test_share_network_subnet_create_metadata(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.78'
        )
        arglist = [
            self.share_network.id,
            '--property', 'Manila=zorilla',
            '--property', 'Zorilla=manila'
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('property', {'Manila': 'zorilla', 'Zorilla': 'manila'}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_subnets_mock.create.assert_called_once_with(
            neutron_net_id=None,
            neutron_subnet_id=None,
            availability_zone=None,
            share_network_id=self.share_network.id,
            metadata={'Manila': 'zorilla', 'Zorilla': 'manila'},
        )
        self.assertEqual(set(self.columns), set(columns))
        self.assertCountEqual(self.data, data)

    def test_share_network_subnet_create_metadata_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.77'
        )
        arglist = [
            self.share_network.id,
            '--property', 'Manila=zorilla',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('property', {'Manila': 'zorilla'})
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareNetworkSubnetDelete(TestShareNetworkSubnet):

    def setUp(self):
        super(TestShareNetworkSubnetDelete, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network

        self.share_network_subnets = (
            manila_fakes.FakeShareNetworkSubnet.create_share_network_subnets())

        self.cmd = osc_share_subnets.DeleteShareNetworkSubnet(
            self.app, None)

    def test_share_network_subnet_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_network_subnets_delete(self):
        arglist = [
            self.share_network.id,
            self.share_network_subnets[0].id,
            self.share_network_subnets[1].id,
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', [self.share_network_subnets[0].id,
                                      self.share_network_subnets[1].id]),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.share_subnets_mock.delete.call_count,
                         len(self.share_network_subnets))
        self.assertIsNone(result)

    def test_share_network_subnet_delete_exception(self):
        arglist = [
            self.share_network.id,
            self.share_network_subnets[0].id,
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', [self.share_network_subnets[0].id]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.share_subnets_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareNetworkSubnetShow(TestShareNetworkSubnet):

    def setUp(self):
        super(TestShareNetworkSubnetShow, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network

        self.share_network_subnet = (
            manila_fakes.FakeShareNetworkSubnet.create_one_share_subnet())
        self.share_subnets_mock.get.return_value = self.share_network_subnet

        self.cmd = osc_share_subnets.ShowShareNetworkSubnet(
            self.app, None)

        self.data = self.share_network_subnet._info.values()
        self.columns = self.share_network_subnet._info.keys()

    def test_share_network_subnet_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_network_subnet_show(self):
        arglist = [
            self.share_network.id,
            self.share_network_subnet.id,
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', self.share_network_subnet.id),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.share_subnets_mock.get.assert_called_once_with(
            self.share_network.id,
            self.share_network_subnet.id
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareNetworkSubnetSet(TestShareNetworkSubnet):

    def setUp(self):
        super(TestShareNetworkSubnetSet, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network

        self.share_network_subnet = (
            manila_fakes.FakeShareNetworkSubnet.create_one_share_subnet())

        self.cmd = osc_share_subnets.SetShareNetworkSubnet(
            self.app, None)

    def test_set_share_network_subnet_property(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.78'
        )
        arglist = [
            self.share_network.id,
            self.share_network_subnet.id,
            '--property', 'Zorilla=manila',
            '--property', 'test=my_test',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', self.share_network_subnet.id),
            ('property', {'Zorilla': 'manila', 'test': 'my_test'}),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_subnets_mock.set_metadata.assert_called_once_with(
            self.share_network.id, {'Zorilla': 'manila', 'test': 'my_test'},
            subresource=self.share_network_subnet.id)

    def test_set_share_network_subnet_property_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.78'
        )
        arglist = [
            self.share_network.id,
            self.share_network_subnet.id,
            '--property', 'key=1',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', self.share_network_subnet.id),
            ('property', {'key': '1'}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_subnets_mock.set_metadata.assert_called_once_with(
            self.share_network.id, {'key': '1'},
            subresource=self.share_network_subnet.id)

        self.share_subnets_mock.set_metadata.side_effect = (
            exceptions.BadRequest)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action,
            parsed_args)


class TestShareNetworkSubnetUnset(TestShareNetworkSubnet):

    def setUp(self):
        super(TestShareNetworkSubnetUnset, self).setUp()

        self.share_network = (
            manila_fakes.FakeShareNetwork.create_one_share_network())
        self.share_networks_mock.get.return_value = self.share_network

        self.share_network_subnet = (
            manila_fakes.FakeShareNetworkSubnet.create_one_share_subnet())

        self.cmd = osc_share_subnets.UnsetShareNetworkSubnet(
            self.app, None)

    def test_unset_share_network_subnet_property(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.78'
        )
        arglist = [
            self.share_network.id,
            self.share_network_subnet.id,
            '--property', 'Manila',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', self.share_network_subnet.id),
            ('property', ['Manila']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_subnets_mock.delete_metadata.assert_called_once_with(
            self.share_network.id, ['Manila'],
            subresource=self.share_network_subnet.id)

    def test_unset_share_network_subnet_property_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            '2.78'
        )
        arglist = [
            self.share_network.id,
            self.share_network_subnet.id,
            '--property', 'Manila',
            '--property', 'test',
        ]
        verifylist = [
            ('share_network', self.share_network.id),
            ('share_network_subnet', self.share_network_subnet.id),
            ('property', ['Manila', 'test']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        self.share_subnets_mock.delete_metadata.assert_has_calls([
            mock.call(self.share_network.id, ['Manila'],
                      subresource=self.share_network_subnet.id),
            mock.call(self.share_network.id, ['test'],
                      subresource=self.share_network_subnet.id)])

        # 404 Not Found would be raised, if property 'Manila' doesn't exist.
        self.share_subnets_mock.delete_metadata.side_effect = (
            exceptions.NotFound)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)
