# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ddt
import mock

from manilaclient import api_versions
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_types

cs = fakes.FakeClient()


@ddt.ddt
class TypesTest(utils.TestCase):

    def _get_share_types_manager(self, microversion):
        version = api_versions.APIVersion(microversion)
        mock_microversion = mock.Mock(api_version=version)
        return share_types.ShareTypeManager(api=mock_microversion)

    @ddt.data(
        {'snapshot_support': 'False'},
        {'snapshot_support': 'False', 'foo': 'bar'},
    )
    def test_init(self, extra_specs):
        info = {'extra_specs': {'snapshot_support': 'False'}}

        share_type = share_types.ShareType(share_types.ShareTypeManager, info)

        self.assertTrue(hasattr(share_type, '_required_extra_specs'))
        self.assertTrue(hasattr(share_type, '_optional_extra_specs'))
        self.assertIsInstance(share_type._required_extra_specs, dict)
        self.assertIsInstance(share_type._optional_extra_specs, dict)
        self.assertEqual(
            {'snapshot_support': 'False'}, share_type.get_optional_keys())

    def test_list_types(self):
        tl = cs.share_types.list()
        cs.assert_called('GET', '/types?is_public=all')
        for t in tl:
            self.assertIsInstance(t, share_types.ShareType)
            self.assertTrue(callable(getattr(t, 'get_required_keys', '')))
            self.assertTrue(callable(getattr(t, 'get_optional_keys', '')))
            self.assertEqual({'test': 'test'}, t.get_required_keys())
            self.assertEqual(
                {'snapshot_support': 'unknown'}, t.get_optional_keys())

    def test_list_types_only_public(self):
        cs.share_types.list(show_all=False)
        cs.assert_called('GET', '/types')

    @ddt.data(
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
        (True, False, False),
        (False, False, True),
        (False, True, False),
        (False, False, False),
    )
    @ddt.unpack
    def test_create(self, is_public, dhss, snapshot_support):
        manager = self._get_share_types_manager("2.7")
        expected_body = {
            "share_type": {
                "name": 'test-type-3',
                'share_type_access:is_public': is_public,
                "extra_specs": {
                    "driver_handles_share_servers": dhss,
                    "snapshot_support": snapshot_support,
                }
            }
        }

        with mock.patch.object(manager, '_create',
                               mock.Mock(return_value="fake")):
            result = manager.create(
                'test-type-3', dhss, snapshot_support, is_public=is_public)

            manager._create.assert_called_once_with(
                "/types", expected_body, "share_type")
            self.assertEqual("fake", result)

    @ddt.data(
        ("2.6", True),
        ("2.7", True),
        ("2.6", False),
        ("2.7", False),
    )
    @ddt.unpack
    def test_create_with_default_values(self, microversion, dhss):
        manager = self._get_share_types_manager(microversion)
        if (api_versions.APIVersion(microversion) >
                api_versions.APIVersion("2.6")):
            is_public_keyname = "share_type_access:is_public"
        else:
            is_public_keyname = "os-share-type-access:is_public"
        expected_body = {
            "share_type": {
                "name": 'test-type-3',
                is_public_keyname: True,
                "extra_specs": {
                    "driver_handles_share_servers": dhss,
                    "snapshot_support": True,
                }
            }
        }

        with mock.patch.object(manager, '_create',
                               mock.Mock(return_value="fake")):
            result = manager.create('test-type-3', dhss)

            manager._create.assert_called_once_with(
                "/types", expected_body, "share_type")
            self.assertEqual("fake", result)

    def test_set_key(self):
        t = cs.share_types.get(1)
        t.set_keys({'k': 'v'})
        cs.assert_called('POST',
                         '/types/1/extra_specs',
                         {'extra_specs': {'k': 'v'}})

    def test_unset_keys(self):
        t = cs.share_types.get(1)
        t.unset_keys(['k'])
        cs.assert_called('DELETE', '/types/1/extra_specs/k')

    def test_delete(self):
        cs.share_types.delete(1)
        cs.assert_called('DELETE', '/types/1')

    def test_get_keys_from_resource_data(self):
        manager = mock.Mock()
        manager.api.client.get = mock.Mock(return_value=(200, {}))
        valid_extra_specs = {'test': 'test'}
        share_type = share_types.ShareType(mock.Mock(),
                                           {'extra_specs': valid_extra_specs,
                                            'name': 'test'},
                                           loaded=True)

        actual_result = share_type.get_keys()

        self.assertEqual(actual_result, valid_extra_specs)
        self.assertEqual(manager.api.client.get.call_count, 0)

    @ddt.data({'prefer_resource_data': True,
               'resource_extra_specs': {}},
              {'prefer_resource_data': False,
               'resource_extra_specs': {'fake': 'fake'}},
              {'prefer_resource_data': False,
              'resource_extra_specs': {}})
    @ddt.unpack
    def test_get_keys_from_api(self, prefer_resource_data,
                               resource_extra_specs):
        manager = mock.Mock()
        valid_extra_specs = {'test': 'test'}
        manager.api.client.get = mock.Mock(
            return_value=(200, {'extra_specs': valid_extra_specs}))
        info = {
            'name': 'test',
            'uuid': 'fake',
            'extra_specs': resource_extra_specs
        }
        share_type = share_types.ShareType(manager, info, loaded=True)

        actual_result = share_type.get_keys(prefer_resource_data)

        self.assertEqual(actual_result, valid_extra_specs)
        self.assertEqual(manager.api.client.get.call_count, 1)
