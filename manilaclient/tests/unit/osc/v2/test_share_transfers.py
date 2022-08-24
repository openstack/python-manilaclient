# Copyright (c) 2022 China Telecom Digital Intelligence.
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

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.osc.v2 import share_transfers as osc_share_transfers
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = [
    'ID',
    'Name',
    'Resource Type',
    'Resource Id',
    'Created At',
    'Source Project Id',
    'Destination Project Id',
    'Accepted',
    'Expires At'
]


class TestShareTransfer(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareTransfer, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.shares_mock.reset_mock()

        self.transfers_mock = self.app.client_manager.share.transfers
        self.transfers_mock.reset_mock()

        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


class TestShareTransferCreate(TestShareTransfer):

    def setUp(self):
        super(TestShareTransferCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.shares_mock.create.return_value = self.share

        self.shares_mock.get.return_value = self.share

        self.share_transfer = (
            manila_fakes.FakeShareTransfer.create_one_transfer())
        self.transfers_mock.get.return_value = self.share_transfer
        self.transfers_mock.create.return_value = self.share_transfer

        self.cmd = osc_share_transfers.CreateShareTransfer(self.app, None)

        self.data = tuple(self.share_transfer._info.values())
        self.columns = tuple(self.share_transfer._info.keys())

    def test_share_transfer_create_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_transfer_create_required_args(self):
        arglist = [
            self.share.id
        ]
        verifylist = [
            ('share', self.share.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.transfers_mock.create.assert_called_with(
            self.share.id,
            name=None
        )

        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareTransferDelete(TestShareTransfer):

    def setUp(self):
        super(TestShareTransferDelete, self).setUp()

        self.transfer = (
            manila_fakes.FakeShareTransfer.create_one_transfer())

        self.transfers_mock.get.return_value = self.transfer

        self.cmd = osc_share_transfers.DeleteShareTransfer(self.app, None)

    def test_share_transfer_delete_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_transfer_delete(self):
        arglist = [
            self.transfer.id
        ]
        verifylist = [
            ('transfer', [self.transfer.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.transfers_mock.delete.assert_called_with(self.transfer.id)
        self.assertIsNone(result)

    def test_share_transfer_delete_multiple(self):
        transfers = (
            manila_fakes.FakeShareTransfer.create_share_transfers(
                count=2))
        arglist = [
            transfers[0].id,
            transfers[1].id
        ]
        verifylist = [
            ('transfer', [transfers[0].id, transfers[1].id])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.assertEqual(self.transfers_mock.delete.call_count,
                         len(transfers))
        self.assertIsNone(result)

    def test_share_transfer_delete_exception(self):
        arglist = [
            self.transfer.id
        ]
        verifylist = [
            ('transfer', [self.transfer.id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.transfers_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(exceptions.CommandError,
                          self.cmd.take_action,
                          parsed_args)


class TestShareTransferShow(TestShareTransfer):

    def setUp(self):
        super(TestShareTransferShow, self).setUp()

        self.transfer = (
            manila_fakes.FakeShareTransfer.create_one_transfer())
        self.transfers_mock.get.return_value = self.transfer

        self.cmd = osc_share_transfers.ShowShareTransfer(self.app, None)

        self.data = self.transfer._info.values()
        self.transfer._info.pop('auth_key')
        self.columns = self.transfer._info.keys()

    def test_share_transfer_show_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_transfer_show(self):
        arglist = [
            self.transfer.id
        ]
        verifylist = [
            ('transfer', self.transfer.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.transfers_mock.get.assert_called_with(self.transfer.id)
        self.assertCountEqual(self.columns, columns)
        self.assertCountEqual(self.data, data)


class TestShareTransferList(TestShareTransfer):

    def setUp(self):
        super(TestShareTransferList, self).setUp()

        self.transfers = (
            manila_fakes.FakeShareTransfer.create_share_transfers(
                count=2))

        self.transfers_mock.list.return_value = self.transfers

        self.values = (oscutils.get_dict_properties(
            m._info, COLUMNS) for m in self.transfers)

        self.cmd = osc_share_transfers.ListShareTransfer(self.app, None)

    def test_list_transfers(self):
        arglist = [
            '--detailed'
        ]
        verifylist = [
            ('detailed', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.transfers_mock.list.assert_called_with(
            detailed=1,
            search_opts={
                'all_tenants': False,
                'id': None,
                'name': None,
                'limit': None,
                'offset': None,
                'resource_type': None,
                'resource_id': None,
                'source_project_id': None},
            sort_key=None,
            sort_dir=None
        )

        self.assertEqual(COLUMNS, columns)
        self.assertEqual(list(self.values), list(data))


class TestShareTransferAccept(TestShareTransfer):

    def setUp(self):
        super(TestShareTransferAccept, self).setUp()

        self.transfer = (
            manila_fakes.FakeShareTransfer.create_one_transfer())

        self.transfers_mock.get.return_value = self.transfer

        self.cmd = osc_share_transfers.AcceptShareTransfer(self.app, None)

    def test_share_transfer_accept_missing_args(self):
        arglist = []
        verifylist = []

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_transfer_accept(self):
        arglist = [
            self.transfer.id,
            self.transfer.auth_key
        ]
        verifylist = [
            ('transfer', self.transfer.id),
            ('auth_key', self.transfer.auth_key)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.transfers_mock.accept.assert_called_with(self.transfer.id,
                                                      self.transfer.auth_key,
                                                      clear_access_rules=False)
        self.assertIsNone(result)
