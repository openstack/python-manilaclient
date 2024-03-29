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


class QuotasV1Test(utils.TestCase):

    def test_import_v1_quotas_module(self):
        try:
            from manilaclient.v1 import quotas
        except Exception as e:
            msg = ("module 'manilaclient.v1.quotas' cannot be imported "
                   "with error: %s") % str(e)
            assert False, msg
        for cls in ('QuotaSet', 'QuotaSetManager'):
            msg = "Module 'quotas' has no '%s' attr." % cls
            self.assertTrue(hasattr(quotas, cls), msg)
