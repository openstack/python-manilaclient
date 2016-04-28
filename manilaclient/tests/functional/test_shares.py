# Copyright 2015 Mirantis Inc.
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

from tempest.lib.common.utils import data_utils

from manilaclient import config
from manilaclient.tests.functional import base

CONF = config.CONF


class SharesReadWriteBase(base.BaseTestCase):
    protocol = None

    @classmethod
    def setUpClass(cls):
        super(SharesReadWriteBase, cls).setUpClass()
        if cls.protocol not in CONF.enable_protocols:
            message = "%s tests are disabled" % cls.protocol
            raise cls.skipException(message)
        cls.name = data_utils.rand_name('autotest_share_name')
        cls.description = data_utils.rand_name('autotest_share_description')

        # NOTE(vponomaryov): following share is used only in one test
        # until tests for snapshots appear.
        cls.share = cls.create_share(
            share_protocol=cls.protocol,
            size=1,
            name=cls.name,
            description=cls.description,
            client=cls.get_user_client(),
            cleanup_in_class=True)

    def test_create_delete_share(self):
        name = data_utils.rand_name('autotest_share_name')

        create = self.create_share(
            self.protocol, name=name, client=self.user_client)

        self.assertEqual(name, create['name'])
        self.assertEqual('1', create['size'])
        self.assertEqual(self.protocol.upper(), create['share_proto'])

        self.user_client.delete_share(create['id'])

        self.user_client.wait_for_share_deletion(create['id'])

    def test_create_update_share(self):
        name = data_utils.rand_name('autotest_share_name')
        new_name = 'new_' + name
        description = data_utils.rand_name('autotest_share_description')
        new_description = 'new_' + description

        create = self.create_share(
            self.protocol, name=name, description=description,
            client=self.user_client)

        self.assertEqual(name, create['name'])
        self.assertEqual(description, create['description'])
        self.assertEqual('False', create['is_public'])

        self.user_client.update_share(
            create['id'], new_name, new_description, True)
        get = self.user_client.get_share(create['id'])

        self.assertEqual(new_name, get['name'])
        self.assertEqual(new_description, get['description'])
        self.assertEqual('True', get['is_public'])

    def test_get_share(self):
        get = self.user_client.get_share(self.share['id'])

        self.assertEqual(self.name, get['name'])
        self.assertEqual(self.description, get['description'])
        self.assertEqual('1', get['size'])
        self.assertEqual(self.protocol.upper(), get['share_proto'])
        self.assertTrue(get.get('export_locations', []) > 0)


class NFSSharesReadWriteTest(SharesReadWriteBase):
    protocol = 'nfs'


class CIFSSharesReadWriteTest(SharesReadWriteBase):
    protocol = 'cifs'


class GlusterFSSharesReadWriteTest(SharesReadWriteBase):
    protocol = 'glusterfs'


class HDFSSharesReadWriteTest(SharesReadWriteBase):
    protocol = 'hdfs'
