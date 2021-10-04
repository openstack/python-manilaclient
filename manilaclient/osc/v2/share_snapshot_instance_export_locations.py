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
from osc_lib import utils

from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils


class ShareSnapshotInstanceExportLocationList(command.Lister):
    """List export locations from a share snapshot instance."""
    _description = _("List export locations from a share snapshot instance.")

    def get_parser(self, prog_name):
        parser = (
            super(ShareSnapshotInstanceExportLocationList, self).get_parser(
                prog_name))
        parser.add_argument(
            "instance",
            metavar="<instance>",
            help=_("Name or ID of the share instance.")
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        snapshot_instance = apiutils.find_resource(
            share_client.share_snapshot_instances, parsed_args.instance)

        share_snapshot_instance_export_locations = (
            share_client.share_snapshot_instance_export_locations.list(
                snapshot_instance=snapshot_instance))

        columns = ["ID", "Path", "Is Admin only"]

        return (
            columns,
            (utils.get_item_properties(s, columns) for s in
             share_snapshot_instance_export_locations))


class ShareSnapshotInstanceExportLocationShow(command.ShowOne):
    """Show export location of the share snapshot instance."""
    _description = _("Show export location of the share snapshot instance.")

    def get_parser(self, prog_name):
        parser = (
            super(ShareSnapshotInstanceExportLocationShow, self).get_parser(
                prog_name))
        parser.add_argument(
            'snapshot_instance',
            metavar='<snapshot_instance>',
            help=_('ID of the share snapshot instance.')
        )
        parser.add_argument(
            'export_location',
            metavar='<export_location>',
            help=_('ID of the share snapshot instance export location.')
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        snapshot_instance = apiutils.find_resource(
            share_client.share_snapshot_instances,
            parsed_args.snapshot_instance)

        share_snapshot_instance_export_location = (
            share_client.share_snapshot_instance_export_locations.get(
                parsed_args.export_location,
                snapshot_instance=snapshot_instance))

        share_snapshot_instance_export_location._info.pop('links', None)

        return self.dict2columns(share_snapshot_instance_export_location._info)
