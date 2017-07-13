# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ddt
import mock

from manilaclient.common.apiclient import auth
from manilaclient.common import constants
from manilaclient.tests.unit import utils


@ddt.ddt
class DiscoverAuthSystems(utils.TestCase):

    @ddt.unpack
    @ddt.data(
        {'plugins': {'a': 42, 'b': 'bar'}, 'discovered': {}},
        {'plugins': {'a': 42, 'b': 'bar'}, 'discovered': {'b': 'overwrite'}},
        {'plugins': {'a': 42, 'b': 'bar'}, 'discovered': {'c': 'reset'}}
    )
    @mock.patch.dict('stevedore.extension.ExtensionManager.ENTRY_POINT_CACHE',
                     clear=True)
    def test_plugins(self, plugins, discovered):
        mock_plugins = []
        for name, return_value in plugins.items():
            plugin = mock.Mock()
            plugin.resolve = mock.Mock(return_value=return_value)
            plugin.name = name
            mock_plugins.append(plugin)
        with mock.patch.dict(
                'manilaclient.common.apiclient.auth._discovered_plugins',
                discovered, clear=True):
            with mock.patch('pkg_resources.iter_entry_points') as ep_mock:
                ep_mock.return_value = mock_plugins
                auth.discover_auth_systems()
                ep_mock.assert_called_with(
                    constants.EXTENSION_PLUGIN_NAMESPACE
                )
                self.assertEqual(plugins, auth._discovered_plugins)
