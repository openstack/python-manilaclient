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


from osc_lib.command import command
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _


class ShareAvailabilityZoneList(command.Lister):
    """List all availability zones."""

    _description = _("List all availability zones")

    def get_parser(self, prog_name):
        parser = super(ShareAvailabilityZoneList, self).get_parser(
            prog_name)
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        availability_zones = share_client.availability_zones.list()

        fields = ("Id", "Name", "Created At", "Updated At")

        return (fields, (oscutils.get_item_properties
                (s, fields) for s in availability_zones))
