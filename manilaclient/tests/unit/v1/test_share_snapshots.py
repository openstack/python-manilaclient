# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2014 Mirantis, Inc.
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
from manilaclient.v1 import share_snapshots


extensions = [
    extension.Extension('share_snapshots', share_snapshots),
]
cs = fakes.FakeClient(extensions=extensions)


@ddt.ddt
class ShareSnapshotsTest(utils.TestCase):

    def test_create_share_snapshot(self):
        cs.share_snapshots.create(1234)
        cs.assert_called('POST', '/snapshots')

    @ddt.data(
        type('SnapshotUUID', (object, ), {'uuid': '1234'}),
        type('SnapshotID', (object, ), {'id': '1234'}),
        '1234')
    def test_get_share_snapshot(self, snapshot):
        snapshot = cs.share_snapshots.get(snapshot)
        cs.assert_called('GET', '/snapshots/1234')

    @ddt.data(
        type('SnapshotUUID', (object, ), {'uuid': '1234'}),
        type('SnapshotID', (object, ), {'id': '1234'}),
        '1234')
    def test_update_share_snapshot(self, snapshot):
        data = dict(foo='bar', quuz='foobar')
        snapshot = cs.share_snapshots.update(snapshot, **data)
        cs.assert_called('PUT', '/snapshots/1234', {'snapshot': data})

    @ddt.data(
        type('SnapshotUUID', (object, ), {'uuid': '1234'}),
        type('SnapshotID', (object, ), {'id': '1234'}),
        '1234')
    def test_reset_snapshot_state(self, snapshot):
        state = 'available'
        expected_body = {'os-reset_status': {'status': 'available'}}
        cs.share_snapshots.reset_state(snapshot, state)
        cs.assert_called('POST', '/snapshots/1234/action', expected_body)

    def test_delete_share_snapshot(self):
        snapshot = cs.share_snapshots.get(1234)
        cs.share_snapshots.delete(snapshot)
        cs.assert_called('DELETE', '/snapshots/1234')

    def test_force_delete_share_snapshot(self):
        snapshot = cs.share_snapshots.get(1234)
        cs.share_snapshots.force_delete(snapshot)
        cs.assert_called('POST', '/snapshots/1234/action',
                         {'os-force_delete': None})

    def test_list_share_snapshots_index(self):
        cs.share_snapshots.list(detailed=False)
        cs.assert_called('GET', '/snapshots')

    def test_list_share_snapshots_index_with_search_opts(self):
        search_opts = {'fake_str': 'fake_str_value', 'fake_int': 1}
        cs.share_snapshots.list(detailed=False, search_opts=search_opts)
        cs.assert_called(
            'GET', '/snapshots?fake_int=1&fake_str=fake_str_value')

    def test_list_share_snapshots_sort_by_asc_and_share_id(self):
        cs.share_snapshots.list(
            detailed=False, sort_key='share_id', sort_dir='asc')
        cs.assert_called('GET', '/snapshots?sort_dir=asc&sort_key=share_id')

    def test_list_share_snapshots_sort_by_desc_and_status(self):
        cs.share_snapshots.list(
            detailed=False, sort_key='status', sort_dir='desc')
        cs.assert_called('GET', '/snapshots?sort_dir=desc&sort_key=status')

    def test_list_share_snapshots_by_improper_direction(self):
        self.assertRaises(ValueError, cs.share_snapshots.list, sort_dir='fake')

    def test_list_share_snapshots_by_improper_key(self):
        self.assertRaises(ValueError, cs.share_snapshots.list, sort_key='fake')

    def test_list_share_snapshots_detail(self):
        cs.share_snapshots.list(detailed=True)
        cs.assert_called('GET', '/snapshots/detail')
