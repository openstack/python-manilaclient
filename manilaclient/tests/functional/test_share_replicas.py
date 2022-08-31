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

from manilaclient import config
from manilaclient.tests.functional import base
from manilaclient.tests.functional import utils

CONF = config.CONF


@utils.skip_if_microversion_not_supported('2.72')
class ShareReplicasTest(base.BaseTestCase):

    def _create_share_and_replica(self):
        replication_type = CONF.replication_type
        share_type = self.create_share_type(
            driver_handles_share_servers=True,
            extra_specs={'replication_type': replication_type})
        share_network = self.create_share_network()
        share = self.create_share(
            share_type=share_type['ID'],
            share_network=share_network['id'],
            client=self.get_user_client())
        share_replica = self.create_share_replica(
            share['id'],
            share_network=share_network['id'],
            wait_for_creation=True,
            client=self.get_user_client())
        return share, share_replica

    def test_share_replica_create(self):
        share, share_replica = self._create_share_and_replica()
        self.assertEqual(share['id'], share_replica['share_id'])

    def test_share_replica_delete(self):
        share, share_replica = self._create_share_and_replica()
        self.user_client.delete_share_replica(share_replica['id'])
        self.user_client.wait_for_share_replica_deletion(share_replica['id'])
