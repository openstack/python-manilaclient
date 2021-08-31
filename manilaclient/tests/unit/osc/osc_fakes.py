#   Copyright 2013 Nebula Inc.
#
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
#

import sys
from unittest import mock

from keystoneauth1 import fixture

AUTH_TOKEN = "foobar"
AUTH_URL = "http://0.0.0.0"
USERNAME = "itchy"
PASSWORD = "scratchy"
PROJECT_NAME = "poochie"
REGION_NAME = "richie"
INTERFACE = "catchy"
VERSION = "3"

TEST_RESPONSE_DICT = fixture.V2Token(token_id=AUTH_TOKEN,
                                     user_name=USERNAME)
_s = TEST_RESPONSE_DICT.add_service('identity', name='keystone')
_s.add_endpoint(AUTH_URL + ':5000/v2.0')
_s = TEST_RESPONSE_DICT.add_service('network', name='neutron')
_s.add_endpoint(AUTH_URL + ':9696')
_s = TEST_RESPONSE_DICT.add_service('compute', name='nova')
_s.add_endpoint(AUTH_URL + ':8774/v2.1')
_s = TEST_RESPONSE_DICT.add_service('image', name='glance')
_s.add_endpoint(AUTH_URL + ':9292')
_s = TEST_RESPONSE_DICT.add_service('object', name='swift')
_s.add_endpoint(AUTH_URL + ':8080/v1')

TEST_RESPONSE_DICT_V3 = fixture.V3Token(user_name=USERNAME)
TEST_RESPONSE_DICT_V3.set_project_scope()

TEST_VERSIONS = fixture.DiscoveryList(href=AUTH_URL)


class FakeStdout(object):

    def __init__(self):
        self.content = []

    def write(self, text):
        self.content.append(text)

    def make_string(self):
        result = ''
        for line in self.content:
            result = result + line
        return result


class FakeLog(object):

    def __init__(self):
        self.messages = {}

    def debug(self, msg):
        self.messages['debug'] = msg

    def info(self, msg):
        self.messages['info'] = msg

    def warning(self, msg):
        self.messages['warning'] = msg

    def error(self, msg):
        self.messages['error'] = msg

    def critical(self, msg):
        self.messages['critical'] = msg


class FakeApp(object):

    def __init__(self, _stdout, _log):
        self.stdout = _stdout
        self.client_manager = None
        self.stdin = sys.stdin
        self.stdout = _stdout or sys.stdout
        self.stderr = sys.stderr
        self.log = _log


class FakeOptions(object):
    def __init__(self, **kwargs):
        self.os_beta_command = False


class FakeClient(object):

    def __init__(self, **kwargs):
        self.endpoint = kwargs['endpoint']
        self.token = kwargs['token']


class FakeClientManager(object):
    _api_version = {
        'image': '2',
    }

    def __init__(self):
        self.compute = None
        self.identity = None
        self.image = None
        self.object_store = None
        self.volume = None
        self.network = None
        self.session = None
        self.auth_ref = None
        self.auth_plugin_name = None
        self.network_endpoint_enabled = True

    def get_configuration(self):
        return {
            'auth': {
                'username': USERNAME,
                'password': PASSWORD,
                'token': AUTH_TOKEN,
            },
            'region': REGION_NAME,
            'identity_api_version': VERSION,
        }

    def is_network_endpoint_enabled(self):
        return self.network_endpoint_enabled


class FakeResource(object):

    def __init__(self, manager=None, info=None, loaded=False, methods=None):
        """Set attributes and methods for a resource.

        :param manager:
            The resource manager
        :param Dictionary info:
            A dictionary with all attributes
        :param bool loaded:
            True if the resource is loaded in memory
        :param Dictionary methods:
            A dictionary with all methods
        """
        info = info or {}
        methods = methods or {}

        self.__name__ = type(self).__name__
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._add_methods(methods)
        self._loaded = loaded

    def _add_details(self, info):
        for (k, v) in info.items():
            setattr(self, k, v)

    def _add_methods(self, methods):
        """Fake methods with MagicMock objects.

        For each <@key, @value> pairs in methods, add an callable MagicMock
        object named @key as an attribute, and set the mock's return_value to
        @value. When users access the attribute with (), @value will be
        returned, which looks like a function call.
        """
        for (name, ret) in methods.items():
            method = mock.Mock(return_value=ret)
            setattr(self, name, method)

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_' and
                          k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def keys(self):
        return self._info.keys()

    def to_dict(self):
        return self._info

    @property
    def info(self):
        return self._info

    def __getitem__(self, item):
        return self._info.get(item)

    def get(self, item, default=None):
        return self._info.get(item, default)


class FakeLimitsResource(FakeResource):

    class AbsoluteLimit:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    class RateLimit:
        def __init__(self, verb, uri, regex, value, remaining,
                     unit, next_available):
            self.verb = verb
            self.uri = uri
            self.regex = regex
            self.value = value
            self.remaining = remaining
            self.unit = unit
            self.next_available = next_available

    @property
    def absolute(self):
        return [
            self.AbsoluteLimit(key, value)
            for key, value in self._info['absolute_limit'].items()
        ]

    @property
    def rate(self):
        rate = self._info['rate_limit']
        return [
            self.RateLimit(
                rate['verb'],
                rate['uri'],
                rate['regex'],
                rate['value'],
                rate['remaining'],
                rate['unit'],
                rate['next-available'])
        ]
