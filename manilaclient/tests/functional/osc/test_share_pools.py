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

from manilaclient.tests.functional.osc import base


class ListSharePoolsTestCase(base.OSCClientTestBase):

    def test_pool_list(self):
        pools = self.list_pools()
        self.assertTableStruct(pools, [
            'Name',
            'Host',
            'Backend',
            'Pool'
        ])
        self.assertTrue(len(pools) > 0)

        # Filter results
        first_pool = pools[0]

        pools = self.list_pools(backend=first_pool['Backend'],
                                host=first_pool['Host'],
                                pool=first_pool['Pool'])
        self.assertEqual(1, len(pools))
        self.assertEqual(first_pool['Name'], pools[0]['Name'])

    def test_pool_list_detail(self):
        pools = self.list_pools(detail=True)
        self.assertTableStruct(pools, [
            'Name',
            'Host',
            'Backend',
            'Pool',
            'Capabilities'
        ])
        self.assertTrue(len(pools) > 0)
