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

from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.osc.v2 import share_access_rules as osc_share_access_rules
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

ACCESS_RULE_ATTRIBUTES = [
    'id',
    'share_id',
    'access_level',
    'access_to',
    'access_type',
    'state',
    'access_key',
    'created_at',
    'updated_at',
    'properties'
]


class TestShareAccess(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareAccess, self).setUp()

        self.shares_mock = self.app.client_manager.share.shares
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)
        self.shares_mock.reset_mock()

        self.access_rules_mock = (
            self.app.client_manager.share.share_access_rules)
        self.access_rules_mock.reset_mock()


class TestShareAccessCreate(TestShareAccess):

    def setUp(self):
        super(TestShareAccessCreate, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share(
            attrs={"is_public": False},
            methods={'allow': None})
        self.shares_mock.get.return_value = self.share
        self.access_rule = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))
        self.share.allow.return_value = self.access_rule._info
        self.access_rules_mock.get.return_value = self.access_rule

        # Get the command object to test
        self.cmd = osc_share_access_rules.ShareAccessAllow(self.app, None)

    def test_share_access_create_user(self):
        arglist = [
            self.share.id,
            'user',
            'demo',
        ]
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={}
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    def test_share_access_create_properties(self):
        arglist = [
            self.share.id,
            'user',
            'demo',
            '--properties', 'key=value'
        ]
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
            ('properties', ['key=value'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={'key': 'value'}
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    def test_access_rule_create_access_level(self):
        arglist = [
            self.share.id,
            'user',
            'demo',
            '--access-level', 'ro'
        ]
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
            ('access_level', 'ro')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level='ro',
            metadata={}
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    def test_share_access_create_wait(self):
        arglist = [
            self.share.id,
            'user',
            'demo',
            '--wait'
        ]
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
            ("wait", True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={}
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    @mock.patch('manilaclient.osc.v2.share_access_rules.LOG')
    def test_share_access_create_wait_error(self, mock_logger):
        arglist = [
            self.share.id,
            'user',
            'demo',
            '--wait'
        ]
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
            ("wait", True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=False):
            columns, data = self.cmd.take_action(parsed_args)

            self.shares_mock.get.assert_called_with(self.share.id)
            self.share.allow.assert_called_with(
                access_type="user",
                access="demo",
                access_level=None,
                metadata={}
            )

            mock_logger.error.assert_called_with(
                "ERROR: Share access rule is in error state.")

            self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
            self.assertCountEqual(self.access_rule._info.values(), data)


class TestShareAccessDelete(TestShareAccess):

    def setUp(self):
        super(TestShareAccessDelete, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share(
            methods={'deny': None})
        self.shares_mock.get.return_value = self.share
        self.access_rule = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))

        # Get the command object to test
        self.cmd = osc_share_access_rules.ShareAccessDeny(self.app, None)

    def test_share_access_delete(self):
        arglist = [
            self.share.id,
            self.access_rule.id
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.deny.assert_called_with(self.access_rule.id)
        self.assertIsNone(result)

    def test_share_access_delete_wait(self):
        arglist = [
            self.share.id,
            self.access_rule.id,
            '--wait'
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.shares_mock.get.assert_called_with(self.share.id)
            self.share.deny.assert_called_with(self.access_rule.id)
            self.assertIsNone(result)

    def test_share_access_delete_wait_error(self):
        arglist = [
            self.share.id,
            self.access_rule.id,
            '--wait'
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id),
            ('wait', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        with mock.patch('osc_lib.utils.wait_for_delete', return_value=False):
            self.assertRaises(
                exceptions.CommandError,
                self.cmd.take_action,
                parsed_args
            )


class TestShareAccessList(TestShareAccess):

    access_rules_columns = [
        'ID',
        'Access Type',
        'Access To',
        'Access Level',
        'State',
        'Access Key',
        'Created At',
        'Updated At'
    ]

    def setUp(self):
        super(TestShareAccessList, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.access_rule_1 = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))
        self.access_rule_2 = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id, "access_to": "admin"}))
        self.access_rules = [self.access_rule_1, self.access_rule_2]

        self.shares_mock.get.return_value = self.share
        self.access_rules_mock.access_list.return_value = self.access_rules
        self.values_list = (oscutils.get_dict_properties(
            a._info, self.access_rules_columns) for a in self.access_rules)

        # Get the command object to test
        self.cmd = osc_share_access_rules.ListShareAccess(self.app, None)

    def test_access_rules_list(self):
        arglist = [
            self.share.id
        ]
        verifylist = [
            ("share", self.share.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.get.assert_called_with(self.share.id)
        self.access_rules_mock.access_list.assert_called_with(
            self.share,
            {})
        self.assertEqual(self.access_rules_columns, columns)
        self.assertEqual(tuple(self.values_list), tuple(data))

    def test_access_rules_list_filter_properties(self):
        arglist = [
            self.share.id,
            '--properties', 'key=value'
        ]
        verifylist = [
            ("share", self.share.id),
            ('properties', ['key=value'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.get.assert_called_with(self.share.id)
        self.access_rules_mock.access_list.assert_called_with(
            self.share,
            {'metadata': {'key': 'value'}})
        self.assertEqual(self.access_rules_columns, columns)
        self.assertEqual(tuple(self.values_list), tuple(data))


class TestShareAccessShow(TestShareAccess):

    def setUp(self):
        super(TestShareAccessShow, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.access_rule = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))
        self.access_rules_mock.get.return_value = self.access_rule

        # Get the command object to test
        self.cmd = osc_share_access_rules.ShowShareAccess(self.app, None)

    def test_access_rule_show(self):
        arglist = [
            self.access_rule.id
        ]
        verifylist = [
            ("access_id", self.access_rule.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.access_rules_mock.get.assert_called_with(self.access_rule.id)
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertEqual(tuple(self.access_rule._info.values()), data)


class TestShareAccessSet(TestShareAccess):

    def setUp(self):
        super(TestShareAccessSet, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.access_rule = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))
        self.access_rules_mock.get.return_value = self.access_rule

        # Get the command object to test
        self.cmd = osc_share_access_rules.SetShareAccess(self.app, None)

    def test_access_rule_set(self):
        arglist = [
            self.access_rule.id,
            '--property', 'key1=value1'
        ]
        verifylist = [
            ("access_id", self.access_rule.id),
            ('property', {'key1': 'value1'})
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.access_rules_mock.set_metadata.assert_called_with(
            self.access_rule,
            {'key1': 'value1'})
        self.assertIsNone(result)


class TestShareAccessUnset(TestShareAccess):

    def setUp(self):
        super(TestShareAccessUnset, self).setUp()

        self.share = manila_fakes.FakeShare.create_one_share()
        self.access_rule = (
            manila_fakes.FakeShareAccessRule.create_one_access_rule(
                attrs={"share_id": self.share.id}))
        self.access_rules_mock.get.return_value = self.access_rule

        # Get the command object to test
        self.cmd = osc_share_access_rules.UnsetShareAccess(self.app, None)

    def test_access_rule_unset(self):
        arglist = [
            self.access_rule.id,
            '--property', 'key1'
        ]
        verifylist = [
            ("access_id", self.access_rule.id),
            ('property', ['key1'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.access_rules_mock.unset_metadata.assert_called_with(
            self.access_rule,
            ['key1'])
        self.assertIsNone(result)
