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

import os
from unittest import mock

import fixtures
import requests
import testtools


class TestCase(testtools.TestCase):
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    def setUp(self):
        super(TestCase, self).setUp()
        if (os.environ.get('OS_STDOUT_CAPTURE') == 'True' or
                os.environ.get('OS_STDOUT_CAPTURE') == '1'):
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if (os.environ.get('OS_STDERR_CAPTURE') == 'True' or
                os.environ.get('OS_STDERR_CAPTURE') == '1'):
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

    def mock_object(self, obj, attr_name, new_attr=None, **kwargs):
        """Mock an object attribute.

        Use python mock to mock an object attribute
        Mocks the specified objects attribute with the given value.
        Automatically performs 'addCleanup' for the mock.
        """
        if not new_attr:
            new_attr = mock.Mock()
        patcher = mock.patch.object(obj, attr_name, new_attr, **kwargs)
        patcher.start()
        self.addCleanup(patcher.stop)
        return new_attr

    def mock_completion(self):
        patcher = mock.patch(
            'manilaclient.base.Manager.write_to_completion_cache')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('manilaclient.base.Manager.completion_cache')
        patcher.start()
        self.addCleanup(patcher.stop)


class TestResponse(requests.Response):
    """Class used to wrap requests.Response.

    Class used to wrap requests.Response and provide some
    convenience to initialize with a dict.
    """

    def __init__(self, data):
        self._text = None
        super(TestResponse, self)
        if isinstance(data, dict):
            self.status_code = data.get('status_code', None)
            self.headers = data.get('headers', {})
            self.headers['x-openstack-request-id'] = data.get(
                'x-openstack-request-id', 'fake-request-id')
            # Fake the text attribute to streamline Response creation
            self._text = data.get('text', None)
        else:
            self.status_code = data
            self.headers = {'x-openstack-request-id': 'fake-request-id'}

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self._text
