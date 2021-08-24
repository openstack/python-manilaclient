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
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _


class ShareReplicaListExportLocation(command.Lister):
    """List export locations of a share replica."""

    _description = _("List export locations of a share replica.")

    def get_parser(self, prog_name):
        parser = super(
            ShareReplicaListExportLocation, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        columns = [
            'ID',
            'Availability Zone',
            'Replica State',
            'Preferred',
            'Path',
        ]

        replica = osc_utils.find_resource(
            share_client.share_replicas,
            parsed_args.replica)

        export_locations = share_client.share_replica_export_locations.list(
            replica)

        data = (osc_utils.get_dict_properties(
            location._info, columns) for location in export_locations)

        return (columns, data)


class ShareReplicaShowExportLocation(command.ShowOne):
    """Show details of a share replica's export location."""

    _description = _("Show details of a share replica's export location.")

    def get_parser(self, prog_name):
        parser = super(
            ShareReplicaShowExportLocation, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica.")
        )
        parser.add_argument(
            "export_location",
            metavar="<export-location>",
            help=_("ID of the share replica export location.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_replicas,
            parsed_args.replica)

        export_location = share_client.share_replica_export_locations.get(
            replica, parsed_args.export_location)

        return self.dict2columns(export_location._info)
