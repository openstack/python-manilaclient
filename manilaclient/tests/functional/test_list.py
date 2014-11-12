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

from manilaclient.tests.functional import base


class ManilaClientTestList(base.BaseTestCase):

    # TODO(vponomaryov): add more tests

    def test_manila_list_by_admin(self):
        self.clients['admin'].manila('list')

    def test_manila_list_by_user(self):
        self.clients['user'].manila('list')
