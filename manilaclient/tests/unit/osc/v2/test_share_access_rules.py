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

import ddt
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


@ddt.ddt
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
            metadata={},
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
            ('properties', ['key=value']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={'key': 'value'},
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    @ddt.data(
        {'lock_visibility': True, 'lock_deletion': True,
         'lock_reason': 'testing resource locks'},
        {'lock_visibility': False, 'lock_deletion': True, 'lock_reason': None},
        {'lock_visibility': True, 'lock_deletion': False, 'lock_reason': None},
    )
    @ddt.unpack
    def test_share_access_create_restrict(self, lock_visibility,
                                          lock_deletion, lock_reason):
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
            ('properties', ['key=value']),
        ]
        allow_call_kwargs = {}
        if lock_visibility:
            arglist.append('--lock-visibility')
            verifylist.append(('lock_visibility', lock_visibility))
            allow_call_kwargs['lock_visibility'] = lock_visibility
        if lock_deletion:
            arglist.append('--lock-deletion')
            verifylist.append(('lock_deletion', lock_deletion))
            allow_call_kwargs['lock_deletion'] = lock_deletion
        if lock_reason:
            arglist.append('--lock-reason')
            arglist.append(lock_reason)
            verifylist.append(('lock_reason', lock_reason))
            allow_call_kwargs['lock_reason'] = lock_reason

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={'key': 'value'},
            **allow_call_kwargs
        )
        self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
        self.assertCountEqual(self.access_rule._info.values(), data)

    @ddt.data(
        {'lock_visibility': True, 'lock_deletion': False},
        {'lock_visibility': False, 'lock_deletion': True},
    )
    @ddt.unpack
    def test_share_access_create_restrict_not_available(
            self, lock_visibility, lock_deletion):
        arglist = [
            self.share.id,
            'user',
            'demo',
        ]
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.79")
        verifylist = [
            ("share", self.share.id),
            ("access_type", "user"),
            ("access_to", "demo"),
            ("lock_visibility", lock_visibility),
            ("lock_deletion", lock_deletion),
            ("lock_reason", None),
        ]
        if lock_visibility:
            arglist.append('--lock-visibility')
        if lock_deletion:
            arglist.append('--lock-deletion')
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

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
            ('access_level', 'ro'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level='ro',
            metadata={},
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
            ("wait", True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.allow.assert_called_with(
            access_type="user",
            access="demo",
            access_level=None,
            metadata={},
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
            ("wait", True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_status', return_value=False):
            columns, data = self.cmd.take_action(parsed_args)

            self.shares_mock.get.assert_called_with(self.share.id)
            self.share.allow.assert_called_with(
                access_type="user",
                access="demo",
                access_level=None,
                metadata={},
            )

            mock_logger.error.assert_called_with(
                "ERROR: Share access rule is in error state.")

            self.assertEqual(ACCESS_RULE_ATTRIBUTES, columns)
            self.assertCountEqual(self.access_rule._info.values(), data)


@ddt.ddt
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

    @ddt.data(True, False)
    def test_share_access_delete(self, unrestrict):
        arglist = [
            self.share.id,
            self.access_rule.id
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id),
        ]
        deny_kwargs = {}
        if unrestrict:
            arglist.append('--unrestrict')
            verifylist.append(("unrestrict", unrestrict))
            deny_kwargs['unrestrict'] = unrestrict
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share.id)
        self.share.deny.assert_called_with(
            self.access_rule.id, **deny_kwargs)
        self.assertIsNone(result)

    def test_share_access_delete_unrestrict_not_available(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.79")
        arglist = [
            self.share.id,
            self.access_rule.id,
            "--unrestrict"
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id),
            ("unrestrict", True)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)

    def test_share_access_delete_wait(self):
        arglist = [
            self.share.id,
            self.access_rule.id,
            '--wait'
        ]
        verifylist = [
            ("share", self.share.id),
            ("id", self.access_rule.id),
            ('wait', True),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        with mock.patch('osc_lib.utils.wait_for_delete', return_value=True):
            result = self.cmd.take_action(parsed_args)

            self.shares_mock.get.assert_called_with(self.share.id)
            self.share.deny.assert_called_with(
                self.access_rule.id)
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


@ddt.ddt
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

    @ddt.data(
        {'access_to': '10.0.0.0/0', 'access_type': 'ip'},
        {'access_key': '10.0.0.0/0', 'access_level': 'rw'},
    )
    def test_access_rules_list_access_filters(self, filters):
        arglist = [
            self.share.id,
        ]

        verifylist = [
            ("share", self.share.id),
        ]
        for filter_key, filter_value in filters.items():
            filter_arg = filter_key.replace("_", "-")
            arglist.append(f'--{filter_arg}')
            arglist.append(filter_value)
            verifylist.append((filter_key, filter_value))

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.get.assert_called_with(self.share.id)
        self.access_rules_mock.access_list.assert_called_with(
            self.share,
            filters)
        self.assertEqual(self.access_rules_columns, columns)
        self.assertEqual(tuple(self.values_list), tuple(data))

    @ddt.data(
        {'access_to': '10.0.0.0/0', 'access_type': 'ip'},
        {'access_key': '10.0.0.0/0', 'access_level': 'rw'},
    )
    def test_access_rules_list_access_filters_command_error(self, filters):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.81")
        arglist = [
            self.share.id,
        ]
        verifylist = [
            ("share", self.share.id),
        ]
        for filter_key, filter_value in filters.items():
            filter_arg = filter_key.replace("_", "-")
            arglist.append(f'--{filter_arg}')
            arglist.append(filter_value)
            verifylist.append((filter_key, filter_value))
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError,
            self.cmd.take_action,
            parsed_args)


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

    def test_access_rule_set_metadata(self):
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

    def test_access_rule_set_access_level(self):
        arglist = [
            self.access_rule.id,
            '--access-level', 'ro'
        ]
        verifylist = [
            ("access_id", self.access_rule.id),
            ('access_level', 'ro')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        self.access_rules_mock.set_access_level.assert_called_with(
            self.access_rule,
            'ro')
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
