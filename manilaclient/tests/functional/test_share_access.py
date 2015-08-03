# Copyright 2015 Mirantis Inc.
# All Rights Reserved.
#
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

from tempest_lib import exceptions as tempest_lib_exc

from manilaclient import config
from manilaclient.tests.functional import base

CONF = config.CONF


class ShareAccessReadWriteBase(base.BaseTestCase):
    protocol = None
    access_level = None

    @classmethod
    def setUpClass(cls):
        super(ShareAccessReadWriteBase, cls).setUpClass()
        if cls.protocol not in CONF.enable_protocols:
            message = "%s tests are disabled." % cls.protocol
            raise cls.skipException(message)
        if cls.access_level not in CONF.access_levels_mapping.get(
                cls.protocol, '').split(' '):
            raise cls.skipException("%(level)s tests for %(protocol)s share "
                                    "access are disabled." % {
                                        'level': cls.access_level,
                                        'protocol': cls.protocol
                                    })
        cls.access_types = CONF.access_types_mapping.get(
            cls.protocol, '').split(' ')
        if not cls.access_types:
            raise cls.skipException("No access levels were provided for %s "
                                    "share access tests." % cls.protoco)

        cls.share = cls.create_share(share_protocol=cls.protocol,
                                     public=True,
                                     cleanup_in_class=True)

        cls.access_to = {
            'ip': '10.0.0.1',
            'user': CONF.username_for_user_rules,
            'cert': 'tenant.example.com',
        }

    def test_list_access_rule_for_share(self):
        access_to = {
            'ip': '10.0.0.1',
            'user': CONF.username_for_user_rules,
            'cert': 'tenant.example.com',
        }
        access_type = self.access_types[0]
        access = self.user_client.access_allow(self.share['id'], access_type,
                                               access_to[access_type],
                                               self.access_level)
        access_list = self.user_client.list_access(self.share['id'])
        self.assertTrue(any(
            [item for item in access_list if access['id'] == item['id']]))

    def _create_delete_access_rule(self, share_id, access_type, access_to):
        access = self.user_client.access_allow(share_id, access_type,
                                               access_to, self.access_level)

        self.assertEqual(share_id, access.get('share_id'))
        self.assertEqual(access_type, access.get('access_type'))
        self.assertEqual(access_to.replace('\\\\', '\\'),
                         access.get('access_to'))
        self.assertEqual(self.access_level, access.get('access_level'))

        self.user_client.wait_for_access_rule_status(share_id, access['id'])
        self.user_client.access_deny(share_id, access['id'])
        self.user_client.wait_for_access_rule_deletion(share_id, access['id'])

        self.assertRaises(tempest_lib_exc.NotFound,
                          self.user_client.get_access, share_id, access['id'])

    def test_create_delete_ip_access_rule(self):
        if 'ip' not in self.access_types:
            raise self.skipException("IP access rule is disabled for protocol "
                                     "%s." % self.protocol)
        self._create_delete_access_rule(self.share['id'], 'ip', '10.0.0.1')

    def test_create_delete_user_access_rule(self):
        if 'user' not in self.access_types:
            raise self.skipException("User access rule is disabled for "
                                     "protocol %s." % self.protocol)
        self._create_delete_access_rule(self.share['id'], 'user',
                                        CONF.username_for_user_rules)

    def test_create_delete_cert_access_rule(self):
        if 'cert' not in self.access_types:
            raise self.skipException("Cert access rule is disabled for "
                                     "protocol %s." % self.protocol)
        self._create_delete_access_rule(self.share['id'], 'cert',
                                        'tenant.example.com')


class NFSShareRWAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'nfs'
    access_level = 'rw'


class NFSShareROAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'nfs'
    access_level = 'ro'


class CIFSShareRWAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'cifs'
    access_level = 'rw'


class CIFSShareROAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'cifs'
    access_level = 'ro'


class GlusterFSShareRWAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'glusterfs'
    access_level = 'rw'


class GlusterFSShareROAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'glusterfs'
    access_level = 'ro'


class HDFSShareRWAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'hdfs'
    access_level = 'rw'


class HDFSShareROAccessReadWriteTest(ShareAccessReadWriteBase):
    protocol = 'hdfs'
    access_level = 'ro'


def load_tests(loader, tests, _):
    result = []
    for test_case in tests:
        if type(test_case._tests[0]) is ShareAccessReadWriteBase:
            continue
        result.append(test_case)
    return loader.suiteClass(result)
