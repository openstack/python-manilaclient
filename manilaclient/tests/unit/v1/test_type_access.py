# Copyright (c) 2013 OpenStack Foundation
#
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

import mock

from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v1 import fakes
from manilaclient.v1 import share_type_access

cs = fakes.FakeClient()

PROJECT_UUID = '11111111-1111-1111-111111111111'


class TypeAccessTest(utils.TestCase):

    def test_list(self):
        share_type = mock.Mock()
        share_type.uuid = '3'
        share_type.is_public = False
        access = cs.share_type_access.list(share_type=share_type)
        cs.assert_called('GET', '/types/3/os-share-type-access')
        for a in access:
            self.assertTrue(isinstance(a, share_type_access.ShareTypeAccess))

    def test_list_public(self):
        share_type = mock.Mock()
        share_type.uuid = '4'
        share_type.is_public = True
        actual_result = cs.share_type_access.list(share_type=share_type)
        self.assertEqual(None, actual_result)

    def test_add_project_access(self):
        cs.share_type_access.add_project_access('3', PROJECT_UUID)
        cs.assert_called('POST', '/types/3/action',
                         {'addProjectAccess': {'project': PROJECT_UUID}})

    def test_remove_project_access(self):
        cs.share_type_access.remove_project_access('3', PROJECT_UUID)
        cs.assert_called('POST', '/types/3/action',
                         {'removeProjectAccess': {'project': PROJECT_UUID}})
