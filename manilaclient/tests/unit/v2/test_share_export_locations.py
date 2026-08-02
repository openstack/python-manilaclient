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

from unittest import mock

import ddt

from manilaclient import api_versions
from manilaclient import extension
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_export_locations


extensions = [
    extension.Extension('share_export_locations', share_export_locations),
]
cs = fakes.FakeClient(extensions=extensions)


@ddt.ddt
class ShareExportLocationsTest(utils.TestCase):
    def _get_manager(self, microversion):
        version = api_versions.APIVersion(microversion)
        mock_microversion = mock.Mock(api_version=version)
        return share_export_locations.ShareExportLocationManager(
            api=mock_microversion
        )

    def test_list_of_export_locations(self):
        share_id = '1234'
        cs.share_export_locations.list(share_id, search_opts=None)
        cs.assert_called('GET', f'/shares/{share_id}/export_locations')

    def test_get_single_export_location(self):
        share_id = '1234'
        el_uuid = 'fake_el_uuid'
        cs.share_export_locations.get(share_id, el_uuid)
        cs.assert_called(
            'GET', (f'/shares/{share_id}/export_locations/{el_uuid}')
        )

    def test_get_metadata(self):
        share_id = '1234'
        el_uuid = 'fake_el_uuid'
        cs.share_export_locations.get_metadata(share_id, el_uuid)
        cs.assert_called(
            'GET',
            f'/shares/{share_id}/export_locations/{el_uuid}/metadata',
        )

    def test_set_metadata(self):
        share_id = '1234'
        el_uuid = 'fake_el_uuid'
        cs.share_export_locations.set_metadata(
            share_id, {'k1': 'v2'}, subresource=el_uuid
        )
        cs.assert_called(
            'POST',
            f'/shares/{share_id}/export_locations/{el_uuid}/metadata',
            {'metadata': {'k1': 'v2'}},
        )

    @ddt.data(
        type('ExportLocationUUID', (object,), {'uuid': 'fake_el_uuid'}),
        type('ExportLocationID', (object,), {'id': 'fake_el_uuid'}),
        'fake_el_uuid',
    )
    def test_delete_metadata(self, export_location):
        share_id = '1234'
        keys = ['key1']
        cs.share_export_locations.delete_metadata(
            share_id, keys, subresource=export_location
        )
        cs.assert_called(
            'DELETE',
            '/shares/1234/export_locations/fake_el_uuid/metadata/key1',
        )

    @ddt.data(
        type('ExportLocationUUID', (object,), {'uuid': 'fake_el_uuid'}),
        type('ExportLocationID', (object,), {'id': 'fake_el_uuid'}),
        'fake_el_uuid',
    )
    def test_update_all_metadata(self, export_location):
        share_id = '1234'
        cs.share_export_locations.update_all_metadata(
            share_id, {'k1': 'v1'}, subresource=export_location
        )
        cs.assert_called(
            'PUT',
            '/shares/1234/export_locations/fake_el_uuid/metadata',
            {'metadata': {'k1': 'v1'}},
        )
