# Copyright (c) 2025 Cloudification GmbH.
#
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

import copy
from unittest import mock

import ddt

from manilaclient import api_versions
from manilaclient.common import constants
from manilaclient import config
from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import qos_types

cs = fakes.FakeClient(api_versions.APIVersion(constants.QOS_TYPE_VERSION))

CONF = config.CONF

LATEST_MICROVERSION = CONF.max_api_microversion


@ddt.ddt
class QosTypesTest(utils.TestCase):
    def setUp(self):
        super().setUp()
        microversion = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
        mock_microversion = mock.Mock(api_version=microversion)
        self.manager = qos_types.QosTypeManager(api=mock_microversion)

    @ddt.data(
        {'expected_iops': '100'},
        {'peak_iops': '500', 'expected_iops': '100'},
    )
    def test_init(self, specs):
        info = {'specs': specs}

        qos_type = qos_types.QosType(qos_types.QosTypeManager, info)

        self.assertTrue(hasattr(qos_type, '_specs'))
        self.assertIsInstance(qos_type._specs, dict)

    def test_list_types(self):
        tl = cs.qos_types.list()
        cs.assert_called('GET', '/qos-types')
        for t in tl:
            t.api_version = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
            self.assertIsInstance(t, qos_types.QosType)
            self.assertTrue(callable(getattr(t, 'get_keys', '')))
            self.assertEqual({'test1': 'test1'}, t.get_keys())

    @ddt.data(
        {'qos_type': 'fixed', 'max_iops': '100'},
        {'qos_type': 'adaptive', 'peak_iops': '200'},
        {'qos_type': 'fixed', 'max_iops': '100', 'expected_iops': '100'},
    )
    def test_create(self, specs):
        specs = copy.copy(specs)

        self.mock_object(
            self.manager, '_create', mock.Mock(return_value="fake")
        )

        result = self.manager.create(
            'test-qos-type-1',
            specs=specs,
        )

        if specs is None:
            specs = {}

        expected_specs = dict(specs)

        expected_body = {
            "qos_type": {
                "name": 'test-qos-type-1',
                "specs": expected_specs,
            }
        }

        self.manager._create.assert_called_once_with(
            "/qos-types", expected_body, "qos_type"
        )
        self.assertEqual("fake", result)

    def test_set_key(self):
        t = cs.qos_types.get(1)
        t.api_version = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
        t.set_keys({'k': 'v'})
        cs.assert_called('POST', '/qos-types/1/specs', {'specs': {'k': 'v'}})

    def test_unset_keys(self):
        t = cs.qos_types.get(1)
        t.api_version = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
        t.unset_keys(['k'])
        cs.assert_called('DELETE', '/qos-types/1/specs/k')

    def test_update(self):
        self.mock_object(
            self.manager, '_update', mock.Mock(return_value="fake")
        )
        qos_type = 1234
        body = dict(description="updated test description")
        expected_body = {
            "qos_type": dict(description="updated test description")
        }
        result = self.manager.update(qos_type, **body)
        self.manager._update.assert_called_once_with(
            f"/qos-types/{qos_type}", expected_body, "qos_type"
        )
        self.assertEqual("fake", result)

    def test_delete(self):
        cs.qos_types.delete(1)
        cs.assert_called('DELETE', '/qos-types/1')

    def test_get_keys_from_resource_data(self):
        version = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
        manager = mock.Mock()
        manager.api = mock.Mock()
        manager.api.client = mock.Mock(return_value=None)
        manager.api.client.get = mock.Mock(return_value=(200, {}))

        valid_specs = {'test': 'test'}
        qos_type = qos_types.QosType(
            manager,
            {'specs': valid_specs, 'name': 'test'},
            loaded=True,
        )
        qos_type.api_version = version

        actual_result = qos_type.get_keys()

        self.assertEqual(actual_result, valid_specs)
        self.assertEqual(manager.api.client.get.call_count, 0)

    @ddt.data(
        {'prefer_resource_data': True, 'resource_specs': {}},
        {
            'prefer_resource_data': False,
            'resource_specs': {'fake': 'fake'},
        },
        {'prefer_resource_data': False, 'resource_specs': {}},
    )
    @ddt.unpack
    def test_get_keys_from_api(self, prefer_resource_data, resource_specs):
        version = api_versions.APIVersion(constants.QOS_TYPE_VERSION)
        manager = mock.Mock()
        manager.api = mock.Mock()
        manager.api.client = mock.Mock(return_value=None)

        valid_specs = {'test': 'test'}
        manager.api.client.get = mock.Mock(
            return_value=(200, {'specs': valid_specs})
        )

        info = {
            'name': 'test',
            'uuid': 'fake',
            'specs': resource_specs,
        }
        qos_type = qos_types.QosType(manager, info, loaded=True)
        qos_type.api_version = version

        actual_result = qos_type.get_keys(prefer_resource_data)

        self.assertEqual(actual_result, valid_specs)
        self.assertEqual(manager.api.client.get.call_count, 1)
