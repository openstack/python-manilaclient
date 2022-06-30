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

from manilaclient.tests.functional.osc import base


class ShareServicesTestCase(base.OSCClientTestBase):

    def test_services_list(self):
        services = self.list_services()
        self.assertTableStruct(services, [
            'ID',
            'Binary',
            'Host',
            'Zone',
            'Status',
            'State',
            'Updated At'
        ])
        self.assertTrue(len(services) > 0)

        # Filter results
        first_service = services[0]

        services = self.list_services(host=first_service['Host'],
                                      status=first_service['Status'],
                                      state=first_service['State'])
        self.assertEqual(1, len(services))
        for attr in ('ID', 'Binary', 'Host', 'State', 'Status', 'Zone'):
            self.assertEqual(first_service[attr], services[0][attr])

    def test_services_set(self):
        services = self.list_services()
        service = [service for service in services if
                   service["Binary"] == "manila-data"]
        first_service = service[0]
        self.openstack(f'share service set {first_service["Host"]} '
                       f'{first_service["Binary"]} '
                       '--disable')
        result = self.listing_result('share service',
                                     'list --status disabled')
        self.assertEqual(first_service['ID'], result[0]['ID'])
        self.assertEqual('disabled', result[0]['Status'])

        # enable the share service again
        self.openstack(f'share service set {first_service["Host"]} '
                       f'{first_service["Binary"]} '
                       '--enable')
