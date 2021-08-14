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

from manilaclient import config
from manilaclient.tests.functional.osc import base
from tempest.lib.common.utils import data_utils

CONF = config.CONF


class ShareReplicasCLITest(base.OSCClientTestBase):

    def _create_share_and_replica(self, add_cleanup=True):
        replication_type = CONF.replication_type
        share_type = self.create_share_type(
            data_utils.rand_name('test_share_type'),
            dhss=True,
            extra_specs={'replication_type': replication_type})
        share_network = self.create_share_network(name='test_share_network')
        share = self.create_share(share_type=share_type['name'],
                                  share_network=share_network['id'])
        replica = self.create_share_replica(share['id'],
                                            share_network=share_network['id'],
                                            wait=True,
                                            add_cleanup=add_cleanup)
        return replica

    def test_share_replica_create(self):
        share_replica = self._create_share_and_replica()
        share_replica_list = self.listing_result('share replica', 'list')
        self.assertTableStruct(share_replica_list, [
            'ID',
            'Status',
            'Share ID',
        ])
        self.assertIn(share_replica['id'],
                      [item['ID'] for item in share_replica_list])

    def test_share_replica_delete(self):
        share_replica = self._create_share_and_replica(add_cleanup=False)
        self.openstack(
            f'share replica delete {share_replica["id"]}'
        )
        self.check_object_deleted('share replica', share_replica["id"])
