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

from osc_lib import exceptions

from openstackclient.tests.unit.identity.v3 import fakes as identity_fakes

from manilaclient.common.apiclient.exceptions import BadRequest
from manilaclient.osc.v2 import share_type_access as osc_share_type_access
from manilaclient.tests.unit.osc.v2 import fakes as manila_fakes


class TestShareTypeAccess(manila_fakes.TestShare):

    def setUp(self):
        super(TestShareTypeAccess, self).setUp()

        self.type_access_mock = (
            self.app.client_manager.share.share_type_access)

        self.type_access_mock.reset_mock()

        self.share_types_mock = self.app.client_manager.share.share_types
        self.share_types_mock.reset_mock()

        self.projects_mock = self.app.client_manager.identity.projects
        self.projects_mock.reset_mock()


class TestShareTypeAccessAllow(TestShareTypeAccess):

    def setUp(self):
        super(TestShareTypeAccessAllow, self).setUp()

        self.project = identity_fakes.FakeProject.create_one_project()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype(
            attrs={'share_type_access:is_public': False})
        self.share_types_mock.get.return_value = self.share_type

        self.type_access_mock.add_project_access.return_value = None

        # Get the command object to test
        self.cmd = osc_share_type_access.ShareTypeAccessAllow(self.app, None)

    def test_share_type_access_create(self):
        arglist = [
            self.share_type.id,
            self.project.id
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('project_id', self.project.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.type_access_mock.add_project_access.assert_called_with(
            self.share_type,
            self.project.id)

        self.assertIsNone(result)

    def test_share_type_access_create_throws_exception(self):
        arglist = [
            self.share_type.id,
            'invalid_project_format'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('project_id', 'invalid_project_format')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.type_access_mock.add_project_access.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeAccessList(TestShareTypeAccess):

    columns = ['Project ID']
    data = (('',), ('',))

    def setUp(self):
        super(TestShareTypeAccessList, self).setUp()

        self.type_access_mock.list.return_value = (
            self.columns, self.data)

        # Get the command object to test
        self.cmd = osc_share_type_access.ListShareTypeAccess(self.app, None)

    def test_share_type_access_list(self):
        share_type = manila_fakes.FakeShareType.create_one_sharetype(
            attrs={'share_type_access:is_public': False})
        self.share_types_mock.get.return_value = share_type

        arglist = [
            share_type.id,
        ]
        verifylist = [
            ('share_type', share_type.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.type_access_mock.list.assert_called_once_with(
            share_type)

        self.assertEqual(self.columns, columns)
        self.assertEqual(self.data, tuple(data))

    def test_share_type_access_list_public_type(self):
        share_type = manila_fakes.FakeShareType.create_one_sharetype(
            attrs={'share_type_access:is_public': True})

        self.share_types_mock.get.return_value = share_type

        arglist = [
            share_type.id,
        ]
        verifylist = [
            ('share_type', share_type.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)


class TestShareTypeAccessDeny(TestShareTypeAccess):

    def setUp(self):
        super(TestShareTypeAccessDeny, self).setUp()

        self.project = identity_fakes.FakeProject.create_one_project()

        self.share_type = manila_fakes.FakeShareType.create_one_sharetype(
            attrs={'share_type_access:is_public': False})
        self.share_types_mock.get.return_value = self.share_type

        self.type_access_mock.remove_project_access.return_value = None

        # Get the command object to test
        self.cmd = osc_share_type_access.ShareTypeAccessDeny(self.app, None)

    def test_share_type_access_delete(self):
        arglist = [
            self.share_type.id,
            self.project.id
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('project_id', self.project.id)
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.type_access_mock.remove_project_access.assert_called_with(
            self.share_type,
            self.project.id)

        self.assertIsNone(result)

    def test_share_type_access_delete_exception(self):
        arglist = [
            self.share_type.id,
            'invalid_project_format'
        ]
        verifylist = [
            ('share_type', self.share_type.id),
            ('project_id', 'invalid_project_format')
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.type_access_mock.remove_project_access.side_effect = BadRequest()
        self.assertRaises(
            exceptions.CommandError, self.cmd.take_action, parsed_args)
