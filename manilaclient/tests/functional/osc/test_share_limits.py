# Copyright 2021 Red Hat, Inc.
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


from manilaclient.tests.functional.osc import base


class ListSharePoolsTestCase(base.OSCClientTestBase):

    def test_limits_show_absolute(self):

        limits = self.listing_result('share', ' limits show --absolute')

        self.assertTableStruct(limits, [
            'Name',
            'Value'
        ])

    def test_limits_show_rate(self):

        limits = self.listing_result('share',
                                     ' limits show --rate --print-empty')

        self.assertTableStruct(limits, [
            'Verb',
            'Regex',
            'URI',
            'Value',
            'Remaining',
            'Unit',
            'Next Available'
        ])
