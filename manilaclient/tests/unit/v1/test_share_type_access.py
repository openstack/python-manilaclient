# Copyright 2016 Mirantis Inc.
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

from manilaclient.tests.unit import utils


class ShareTypeAccessV1Test(utils.TestCase):

    def test_import_v1_share_type_access_module(self):
        try:
            from manilaclient.v1 import share_type_access
        except Exception as e:
            msg = ("module 'manilaclient.v1.share_type_access' cannot be "
                   "imported with error: %s") % str(e)
            assert False, msg
        for cls in ('ShareTypeAccess', 'ShareTypeAccessManager'):
            msg = "Module 'share_type_access' has no '%s' attr." % cls
            self.assertTrue(hasattr(share_type_access, cls), msg)
