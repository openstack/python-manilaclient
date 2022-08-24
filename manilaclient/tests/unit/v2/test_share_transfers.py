# Copyright (c) 2022 China Telecom Digital Intelligence.
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

from manilaclient import api_versions
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes

TRANSFER_URL = 'share-transfers'
cs = fakes.FakeClient(api_versions.APIVersion('2.77'))


class ShareTransfersTest(utils.TestCase):

    def test_create(self):
        cs.transfers.create('1234')
        cs.assert_called('POST', '/%s' % TRANSFER_URL,
                         body={'transfer': {'share_id': '1234',
                                            'name': None}})

    def test_get(self):
        transfer_id = '5678'
        cs.transfers.get(transfer_id)
        cs.assert_called('GET', '/%s/%s' % (TRANSFER_URL, transfer_id))

    def test_list(self):
        cs.transfers.list()
        cs.assert_called('GET', '/%s/detail' % TRANSFER_URL)

    def test_delete(self):
        cs.transfers.delete('5678')
        cs.assert_called('DELETE', '/%s/5678' % TRANSFER_URL)

    def test_accept(self):
        transfer_id = '5678'
        auth_key = '12345'
        cs.transfers.accept(transfer_id, auth_key)
        cs.assert_called('POST',
                         '/%s/%s/accept' % (TRANSFER_URL, transfer_id))
