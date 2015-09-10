# Copyright 2015 Mirantis inc.
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

import ddt

from manilaclient import extension
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v1 import fakes
from manilaclient.v1 import share_instances


extensions = [
    extension.Extension('share_instances', share_instances),
]
cs = fakes.FakeClient(extensions=extensions)


@ddt.ddt
class ShareInstancesTest(utils.TestCase):

    def test_list(self):
        cs.share_instances.list()
        cs.assert_called('GET', '/share_instances')

    def test_get(self):
        instance = type('None', (object, ), {'id': '1234'})
        cs.share_instances.get(instance)
        cs.assert_called('GET', '/share_instances/1234')

    def test_force_delete(self):
        instance = cs.share_instances.get('1234')
        cs.share_instances.force_delete(instance)
        cs.assert_called('POST', '/share_instances/1234/action',
                         {'os-force_delete': None})

    def test_reset_state(self):
        state = 'available'
        expected_body = {'os-reset_status': {'status': 'available'}}
        instance = cs.share_instances.get('1234')
        cs.share_instances.reset_state(instance, state)
        cs.assert_called('POST', '/share_instances/1234/action', expected_body)