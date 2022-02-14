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
from manilaclient.common.apiclient.exceptions import BadRequest
from manilaclient.common.apiclient.exceptions import NotFound
from manilaclient.osc import utils
from manilaclient.osc.v2 import share_types as osc_share_types
from manilaclient.tests.unit.osc import osc_utils
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes

COLUMNS = [
    'id',
    'name',
    'visibility',
    'is_default',
    'required_extra_specs',
    'optional_extra_specs',
    'description'
]


class TestShareType(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareType, self).setUp()

        self.shares_mock = self.app.client_manager.share.share_types
        self.shares_mock.reset_mock()
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            api_versions.MAX_VERSION)


class TestShareTypeCreate(TestShareType):

    def setUp(self):
        super(TestShareTypeCreate, self).setUp()

        self.new_share_type = manila_fakes.FakeShareType.create_one_sharetype()
        self.shares_mock.create.return_value = self.new_share_type

        # Get the command object to test
        self.cmd = osc_share_types.CreateShareType(self.app, None)

        self.data = [
            self.new_share_type.id,
            self.new_share_type.name,
            'public',
            self.new_share_type.is_default,
            'driver_handles_share_servers : True',
            ('replication_type : readable\n'
             'mount_snapshot_support : False\n'
             'revert_to_snapshot_support : False\n'
             'create_share_from_snapshot_support : True\n'
             'snapshot_support : True'),
            self.new_share_type.description,
        ]

        self.raw_data = [
            self.new_share_type.id,
            self.new_share_type.name,
            'public',
            self.new_share_type.is_default,
            {'driver_handles_share_servers': True},
            {'replication_type': 'readable',
             'mount_snapshot_support': False,
             'revert_to_snapshot_support': False,
             'create_share_from_snapshot_support': True,
             'snapshot_support': True},
            self.new_share_type.description,
        ]

    def test_share_type_create_required_args(self):
        """Verifies required arguments."""

        arglist = [
            self.new_share_type.name,
            'True'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            extra_specs={},
            is_public=True,
            name=self.new_share_type.name,
            spec_driver_handles_share_servers=True
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_share_type_create_json_fomrat(self):
        """Verifies --format json."""

        arglist = [
            self.new_share_type.name,
            'True',
            '-f', 'json'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            extra_specs={},
            is_public=True,
            name=self.new_share_type.name,
            spec_driver_handles_share_servers=True
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.raw_data, data)

    def test_share_type_create_missing_required_arg(self):
        """Verifies missing required arguments."""

        arglist = [
            self.new_share_type.name
        ]
        verifylist = [
            ('name', self.new_share_type.name)
        ]

        self.assertRaises(osc_utils.ParserException,
                          self.check_parser, self.cmd, arglist, verifylist)

    def test_share_type_create_private(self):
        arglist = [
            self.new_share_type.name,
            'True',
            '--public', 'False'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True'),
            ('public', 'False')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            extra_specs={},
            is_public=False,
            name=self.new_share_type.name,
            spec_driver_handles_share_servers=True
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_share_type_create_extra_specs(self):
        arglist = [
            self.new_share_type.name,
            'True',
            '--extra-specs', 'snapshot_support=true'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True'),
            ('extra_specs', ['snapshot_support=true'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            extra_specs={'snapshot_support': 'True'},
            is_public=True,
            name=self.new_share_type.name,
            spec_driver_handles_share_servers=True
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_share_type_create_dhss_invalid_value(self):
        arglist = [
            self.new_share_type.name,
            'non_bool_value'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'non_bool_value')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_type_create_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.40")

        arglist = [
            self.new_share_type.name,
            'True',
            '--description', 'Description'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True'),
            ('description', 'Description')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_type_create_dhss_defined_twice(self):
        arglist = [
            self.new_share_type.name,
            'True',
            '--extra-specs', 'driver_handles_share_servers=true'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True'),
            ('extra_specs', ['driver_handles_share_servers=true'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_type_create_bool_args(self):
        arglist = [
            self.new_share_type.name,
            'True',
            '--snapshot-support', 'true'
        ]
        verifylist = [
            ('name', self.new_share_type.name),
            ('spec_driver_handles_share_servers', 'True'),
            ('snapshot_support', 'true')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)

        self.shares_mock.create.assert_called_with(
            extra_specs={'snapshot_support': 'True'},
            is_public=True,
            name=self.new_share_type.name,
            spec_driver_handles_share_servers=True
        )

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)


class TestShareTypeDelete(TestShareType):

    share_types = manila_fakes.FakeShareType.create_share_types(count=2)

    def setUp(self):
        super(TestShareTypeDelete, self).setUp()

        self.shares_mock.get = manila_fakes.FakeShareType.get_share_types(
            self.share_types)
        self.shares_mock.delete.return_value = None

        # Get the command object to test
        self.cmd = osc_share_types.DeleteShareType(self.app, None)

    def test_share_type_delete_one(self):
        arglist = [
            self.share_types[0].id
        ]

        verifylist = [
            ('share_types', [self.share_types[0].id])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.shares_mock.delete.assert_called_with(self.share_types[0])
        self.assertIsNone(result)

    def test_share_type_delete_multiple(self):
        arglist = []
        for t in self.share_types:
            arglist.append(t.id)
        verifylist = [
            ('share_types', arglist),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)

        calls = []
        for t in self.share_types:
            calls.append(mock.call(t))
        self.shares_mock.delete.assert_has_calls(calls)
        self.assertIsNone(result)

    def test_delete_share_type_with_exception(self):
        arglist = [
            'non_existing_type',
        ]
        verifylist = [
            ('share_types', arglist),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.shares_mock.delete.side_effect = exceptions.CommandError()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeSet(TestShareType):

    def setUp(self):
        super(TestShareTypeSet, self).setUp()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype(
            methods={'set_keys': None, 'update': None})
        self.shares_mock.get.return_value = self.share_type

        # Get the command object to test
        self.cmd = osc_share_types.SetShareType(self.app, None)

    def test_share_type_set_extra_specs(self):
        arglist = [
            self.share_type.id,
            '--extra-specs', 'snapshot_support=true'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('extra_specs', ['snapshot_support=true'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.share_type.set_keys.assert_called_with(
            {'snapshot_support': 'True'})
        self.assertIsNone(result)

    def test_share_type_set_name(self):
        arglist = [
            self.share_type.id,
            '--name', 'new name'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('name', 'new name')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.share_type.update.assert_called_with(
            name='new name')
        self.assertIsNone(result)

    def test_share_type_set_description(self):
        arglist = [
            self.share_type.id,
            '--description', 'new description'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('description', 'new description')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.share_type.update.assert_called_with(
            description='new description')
        self.assertIsNone(result)

    def test_share_type_set_visibility(self):
        arglist = [
            self.share_type.id,
            '--public', 'false'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('public', 'false')
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.share_type.update.assert_called_with(
            is_public=False)
        self.assertIsNone(result)

    def test_share_type_set_extra_specs_exception(self):
        arglist = [
            self.share_type.id,
            '--extra-specs', 'snapshot_support=true'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('extra_specs', ['snapshot_support=true'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.share_type.set_keys.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)

    def test_share_type_set_api_version_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.49")

        arglist = [
            self.share_type.id,
            '--name', 'new name',
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('name', 'new name'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeUnset(TestShareType):

    def setUp(self):
        super(TestShareTypeUnset, self).setUp()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype(
            methods={'unset_keys': None})
        self.shares_mock.get.return_value = self.share_type

        # Get the command object to test
        self.cmd = osc_share_types.UnsetShareType(self.app, None)

    def test_share_type_unset_extra_specs(self):
        arglist = [
            self.share_type.id,
            'snapshot_support'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('extra_specs', ['snapshot_support'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)
        self.share_type.unset_keys.assert_called_with(['snapshot_support'])
        self.assertIsNone(result)

    def test_share_type_unset_exception(self):
        arglist = [
            self.share_type.id,
            'snapshot_support'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('extra_specs', ['snapshot_support'])
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.share_type.unset_keys.side_effect = NotFound()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeList(TestShareType):

    share_types = manila_fakes.FakeShareType.create_share_types()
    columns = utils.format_column_headers(COLUMNS)

    def setUp(self):
        super(TestShareTypeList, self).setUp()

        self.shares_mock.list.return_value = self.share_types

        # Get the command object to test
        self.cmd = osc_share_types.ListShareType(self.app, None)

        self.values = (oscutils.get_dict_properties(
            s._info, COLUMNS) for s in self.share_types)

    def test_share_type_list_no_options(self):
        arglist = []
        verifylist = [
            ('all', False)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.list.assert_called_once_with(
            search_opts={},
            show_all=False
        )
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_type_list_all(self):
        arglist = [
            '--all',
        ]
        verifylist = [
            ('all', True)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.list.assert_called_once_with(
            search_opts={},
            show_all=True)
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_type_list_extra_specs(self):
        arglist = [
            '--extra-specs', 'snapshot_support=true'
        ]
        verifylist = [
            ('extra_specs', ['snapshot_support=true'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.list.assert_called_once_with(
            search_opts={'extra_specs': {'snapshot_support': 'True'}},
            show_all=False)
        self.assertEqual(self.columns, columns)
        self.assertEqual(list(self.values), list(data))

    def test_share_type_list_api_versions_exception(self):
        self.app.client_manager.share.api_version = api_versions.APIVersion(
            "2.42")

        arglist = [
            '--extra-specs', 'snapshot_support=true'
        ]
        verifylist = [
            ('extra_specs', ['snapshot_support=true'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeShow(TestShareType):

    def setUp(self):
        super(TestShareTypeShow, self).setUp()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype()

        self.shares_mock.get.return_value = self.share_type

        # Get the command object to test
        self.cmd = osc_share_types.ShowShareType(self.app, None)

        self.data = [
            self.share_type.id,
            self.share_type.name,
            'public',
            self.share_type.is_default,
            'driver_handles_share_servers : True',
            ('replication_type : readable\n'
             'mount_snapshot_support : False\n'
             'revert_to_snapshot_support : False\n'
             'create_share_from_snapshot_support : True\n'
             'snapshot_support : True'),
            self.share_type.description,
        ]

        self.raw_data = [
            self.share_type.id,
            self.share_type.name,
            'public',
            self.share_type.is_default,
            {'driver_handles_share_servers': True},
            {'replication_type': 'readable',
             'mount_snapshot_support': False,
             'revert_to_snapshot_support': False,
             'create_share_from_snapshot_support': True,
             'snapshot_support': True},
            self.share_type.description,
        ]

    def test_share_type_show(self):
        arglist = [
            self.share_type.id
        ]
        verifylist = [
            ("share_type", self.share_type.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share_type.id)

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.data, data)

    def test_share_type_show_json_format(self):
        arglist = [
            self.share_type.id,
            '-f', 'json',
        ]
        verifylist = [
            ("share_type", self.share_type.id)
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.shares_mock.get.assert_called_with(self.share_type.id)

        self.assertCountEqual(COLUMNS, columns)
        self.assertCountEqual(self.raw_data, data)
