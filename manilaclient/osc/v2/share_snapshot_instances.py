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
from osc_lib import exceptions
from osc_lib import utils

from manilaclient.common._i18n import _
from manilaclient.common import cliutils


class ListShareSnapshotInstance(command.Lister):
    """List all share snapshot instances."""
    _description = _("List all share snapshot instances")

    def get_parser(self, prog_name):
        parser = super(ListShareSnapshotInstance, self).get_parser(
            prog_name)
        parser.add_argument(
            "--snapshot",
            metavar="<snapshot>",
            default=None,
            help=_("Filter results by share snapshot ID.")
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help=_("Show detailed information about snapshot instances. ")
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        snapshot = (share_client.share_snapshots.get(parsed_args.snapshot)
                    if parsed_args.snapshot else None)

        share_snapshot_instances = share_client.share_snapshot_instances.list(
            detailed=parsed_args.detailed,
            snapshot=snapshot,
        )

        list_of_keys = ['ID', 'Snapshot ID', 'Status']

        if (parsed_args.detailed):
            list_of_keys += ['Created At', 'Updated At', 'Share ID',
                             'Share Instance ID', 'Progress',
                             'Provider Location']

        return (list_of_keys, (utils.get_item_properties
                (s, list_of_keys) for s in share_snapshot_instances))


class ShowShareSnapshotInstance(command.ShowOne):
    """Show details about a share snapshot instance."""
    _description = _("Show details about a share snapshot instance.")

    def get_parser(self, prog_name):
        parser = super(ShowShareSnapshotInstance, self).get_parser(
            prog_name)
        parser.add_argument(
            "snapshot_instance",
            metavar="<snapshot_instance>",
            help=_("ID of the share snapshot instance.")
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        snapshot_instance = share_client.share_snapshot_instances.get(
            parsed_args.snapshot_instance)

        snapshot_instance_export_locations = (
            share_client.share_snapshot_instance_export_locations.list(
                snapshot_instance=snapshot_instance))

        snapshot_instance._info['export_locations'] = []
        for element_location in snapshot_instance_export_locations:
            element_location._info.pop('links', None)
            snapshot_instance._info['export_locations'].append(
                element_location._info)

        if parsed_args.formatter == 'table':
            snapshot_instance._info['export_locations'] = (
                cliutils.convert_dict_list_to_string(
                    snapshot_instance._info['export_locations']))

        snapshot_instance._info.pop('links', None)

        return self.dict2columns(snapshot_instance._info)


class SetShareSnapshotInstance(command.Command):
    """Explicitly update the state of a share snapshot instance."""
    _description = _("Explicitly update the state of a share snapshot "
                     "instance.")

    def get_parser(self, prog_name):
        parser = super(SetShareSnapshotInstance, self).get_parser(
            prog_name)
        parser.add_argument(
            "snapshot_instance",
            metavar="<snapshot_instance>",
            help=_("ID of the share snapshot instance to update.")
        )
        parser.add_argument(
            '--status',
            metavar='<status>',
            default='available',
            choices=['available', 'error', 'creating', 'deleting',
                     'error_deleting'],
            help=_('Indicate state to update the snapshot instance to. '
                   'Default is available.')
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        try:
            share_client.share_snapshot_instances.reset_state(
                parsed_args.snapshot_instance, parsed_args.status)
        except Exception as e:
            msg = _(
                "Failed to update share snapshot instance status: %s" % e)
            raise exceptions.CommandError(msg)
