# Copyright 2019 Red Hat, Inc.
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

import logging

from openstackclient.identity import common as identity_common
from osc_lib.cli import format_columns
from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import cliutils
from manilaclient.osc import utils

LOG = logging.getLogger(__name__)

SHARE_ATTRIBUTES = [
    'id',
    'name',
    'size',
    'share_proto',
    'status',
    'is_public',
    'share_type_name',
    'availability_zone',
    'description',
    'share_network_id',
    'share_server_id',
    'share_type',
    'share_group_id',
    'host',
    'user_id',
    'project_id',
    'access_rules_status',
    'snapshot_id',
    'snapshot_support',
    'create_share_from_snapshot_support',
    'mount_snapshot_support',
    'revert_to_snapshot_support',
    'task_state',
    'source_share_group_snapshot_member_id',
    'replication_type',
    'has_replicas',
    'created_at',
    'metadata'
]

SHARE_ATTRIBUTES_HEADERS = [
    'ID',
    'Name',
    'Size',
    'Share Protocol',
    'Status',
    'Is Public',
    'Share Type Name',
    'Availability Zone',
    'Description',
    'Share Network ID',
    'Share Server ID',
    'Share Type',
    'Share Group ID',
    'Host',
    'User ID',
    'Project ID',
    'Access Rules Status',
    'Source Snapshot ID',
    'Supports Creating Snapshots',
    'Supports Cloning Snapshots',
    'Supports Mounting snapshots',
    'Supports Reverting to Snapshot',
    'Migration Task Status',
    'Source Share Group Snapshot Member ID',
    'Replication Type',
    'Has Replicas',
    'Created At',
    'Properties',
]


class CreateShare(command.ShowOne):
    """Create a new share."""
    _description = _("Create new share")

    log = logging.getLogger(__name__ + ".CreateShare")

    def get_parser(self, prog_name):
        parser = super(CreateShare, self).get_parser(prog_name)
        parser.add_argument(
            'share_proto',
            metavar="<share_protocol>",
            help=_('Share protocol (NFS, CIFS, CephFS, GlusterFS or HDFS)')
        )
        parser.add_argument(
            'size',
            metavar="<size>",
            type=int,
            help=_('Share size in GiB.')
        )
        parser.add_argument(
            '--name',
            metavar="<name>",
            default=None,
            help=_('Optional share name. (Default=None)')
        )
        parser.add_argument(
            '--snapshot-id',
            metavar="<snapshot-id>",
            default=None,
            help=_("Optional snapshot ID to create the share from."
                   " (Default=None)")
        )
        # NOTE(vkmc) --property replaces --metadata in osc
        parser.add_argument(
            "--property",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_("Set a property to this share "
                   "(repeat option to set multiple properties)"),
        )
        parser.add_argument(
            '--share-network',
            metavar='<network-info>',
            default=None,
            help=_('Optional network info ID or name.'),
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_('Optional share description. (Default=None)')
        )
        parser.add_argument(
            '--public',
            default=False,
            help=_('Level of visibility for share. '
                   'Defines whether other tenants are able to see it or not.')
        )
        parser.add_argument(
            '--share-type',
            metavar='<share-type>',
            default=None,
            help=_('Optional share type. Use of optional shares type '
                   'is deprecated. (Default=Default)')
        )
        parser.add_argument(
            '--availability-zone',
            metavar='<availability-zone>',
            default=None,
            help=_('Availability zone in which share should be created.')
        )
        parser.add_argument(
            '--share-group',
            metavar='<share-group>',
            default=None,
            help=_('Optional share group name or ID in which to create '
                   'the share. (Experimental, Default=None).')
        )
        return parser

    def take_action(self, parsed_args):
        # TODO(s0ru): the table shows 'Field', 'Value'
        share_client = self.app.client_manager.share

        share_type = None
        if parsed_args.share_type:
            share_type = apiutils.find_resource(share_client.share_types,
                                                parsed_args.share_type).id

        share_network = None
        if parsed_args.share_network:
            share_network = apiutils.find_resource(
                share_client.share_networks,
                parsed_args.share_network).id

        share_group = None
        if parsed_args.share_group:
            share_group = apiutils.find_resource(share_client.share_groups,
                                                 parsed_args.share_group).id

        size = parsed_args.size

        snapshot_id = None
        if parsed_args.snapshot_id:
            snapshot = apiutils.find_resource(share_client.share_snapshots,
                                              parsed_args.snapshot_id)
            size = max(size or 0, snapshot.size)

        body = {
            'share_proto': parsed_args.share_proto,
            'size': parsed_args.size,
            'snapshot_id': snapshot_id,
            'name': parsed_args.name,
            'description': parsed_args.description,
            'metadata': parsed_args.property,
            'share_network': share_network,
            'share_type': share_type,
            'is_public': parsed_args.public,
            'availability_zone': parsed_args.availability_zone,
            'share_group_id': share_group
        }

        share = share_client.shares.create(**body)

        printable_share = share._info
        printable_share.pop('links', None)
        printable_share.pop('shares_type', None)

        return self.dict2columns(printable_share)


class DeleteShare(command.Command):
    """Delete a share."""
    _description = _("Delete a share")

    def get_parser(self, prog_name):
        parser = super(DeleteShare, self).get_parser(prog_name)
        parser.add_argument(
            "shares",
            metavar="<share>",
            nargs="+",
            help=_("Share(s) to delete (name or ID)")
        )
        parser.add_argument(
            "--share-group",
            metavar="<share-group>",
            default=None,
            help=_("Optional share group (name or ID)"
                   "which contains the share")
        )
        parser.add_argument(
            "--force",
            action='store_true',
            default=False,
            help=_("Attempt forced removal of share(s), regardless of state "
                   "(defaults to False)")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for share in parsed_args.shares:
            try:
                share_obj = apiutils.find_resource(
                    share_client.shares, share
                )
                share_group_id = (share_group_id if parsed_args.share_group
                                  else None)
                if parsed_args.force:
                    share_client.shares.force_delete(share_obj)
                else:
                    share_client.shares.delete(share_obj,
                                               share_group_id)
            except Exception as exc:
                result += 1
                LOG.error(_("Failed to delete share with "
                            "name or ID '%(share)s': %(e)s"),
                          {'share': share, 'e': exc})

        if result > 0:
            total = len(parsed_args.shares)
            msg = (_("%(result)s of %(total)s shares failed "
                   "to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ListShare(command.Lister):
    """List Shared file systems (shares)."""
    _description = _("List shares")

    def get_parser(self, prog_name):
        parser = super(ListShare, self).get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar="<share-name>",
            help=_('Filter shares by share name')
        )
        parser.add_argument(
            '--status',
            metavar="<share-status>",
            help=_('Filter shares by status')
        )
        parser.add_argument(
            '--snapshot',
            metavar='<share-network-id>',
            help=_('Filter shares by snapshot name or id.'),
        )
        parser.add_argument(
            '--public',
            action='store_true',
            default=False,
            help=_('Include public shares'),
        )
        parser.add_argument(
            '--share-network',
            metavar='<share-network-name-or-id>',
            help=_('Filter shares exported on a given share network'),
        )
        parser.add_argument(
            '--share-type',
            metavar='<share-type-name-or-id>',
            help=_('Filter shares of a given share type'),
        )
        parser.add_argument(
            '--share-group',
            metavar='<share-group-name-or-id>',
            help=_('Filter shares belonging to a given share group'),
        )
        parser.add_argument(
            '--host',
            metavar='<share-host>',
            help=_('Filter shares belonging to a given host (admin only)'),
        )
        parser.add_argument(
            '--share-server',
            metavar='<share-server-id>',
            help=_('Filter shares exported via a given share server '
                   '(admin only)'),
        )
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_('Filter shares by project (name or ID) (admin only)')
        )
        identity_common.add_project_domain_option_to_parser(parser)
        parser.add_argument(
            '--user',
            metavar='<user>',
            help=_('Filter results by user (name or ID) (admin only)')
        )
        identity_common.add_user_domain_option_to_parser(parser)
        parser.add_argument(
            '--all-projects',
            action='store_true',
            default=False,
            help=_('Include all projects (admin only)'),
        )
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help=_('Filter shares having a given metadata key=value property '
                   '(repeat option to filter by multiple properties)'),
        )
        parser.add_argument(
            '--extra-spec',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            help=_('Filter shares with extra specs (key=value) of the share '
                   'type that they belong to. '
                   '(repeat option to filter by multiple extra specs)'),
        )
        parser.add_argument(
            '--long',
            action='store_true',
            default=False,
            help=_('List additional fields in output'),
        )
        parser.add_argument(
            '--sort',
            metavar="<key>[:<direction>]",
            default='name:asc',
            help=_("Sort output by selected keys and directions(asc or desc) "
                   "(default: name:asc), multiple keys and directions can be "
                   "specified separated by comma"),
        )
        parser.add_argument(
            '--limit',
            metavar="<num-shares>",
            type=int,
            action=parseractions.NonNegativeAction,
            help=_('Maximum number of shares to display'),
        )
        parser.add_argument(
            '--marker',
            metavar="<share>",
            help=_('The last share ID of the previous page'),
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        # TODO(gouthamr): Add support for ~name, ~description
        # export_location filtering
        if parsed_args.long:
            columns = SHARE_ATTRIBUTES
            column_headers = SHARE_ATTRIBUTES_HEADERS
        else:
            columns = [
                'id',
                'name',
                'size',
                'share_proto',
                'status',
                'is_public',
                'share_type_name',
                'host',
                'availability_zone'
            ]
            column_headers = [
                'ID',
                'Name',
                'Size',
                'Share Proto',
                'Status',
                'Is Public',
                'Share Type Name',
                'Host',
                'Availability Zone'
            ]

        project_id = None
        if parsed_args.project:
            project_id = identity_common.find_project(
                identity_client,
                parsed_args.project,
                parsed_args.project_domain).id

        user_id = None
        if parsed_args.user:
            user_id = identity_common.find_user(identity_client,
                                                parsed_args.user,
                                                parsed_args.user_domain).id

        # set value of 'all_projects' when using project option
        all_projects = bool(parsed_args.project) or parsed_args.all_projects

        share_type_id = None
        if parsed_args.share_type:
            share_type_id = apiutils.find_resource(share_client.share_types,
                                                   parsed_args.share_type).id

        snapshot_id = None
        if parsed_args.snapshot:
            snapshot_id = apiutils.find_resource(share_client.share_snapshots,
                                                 parsed_args.snapshot).id

        share_network_id = None
        if parsed_args.share_network:
            share_network_id = apiutils.find_resource(
                share_client.share_networks,
                parsed_args.share_network).id

        share_group_id = None
        if parsed_args.share_group:
            share_group_id = apiutils.find_resource(share_client.share_groups,
                                                    parsed_args.share_group).id

        share_server_id = None
        if parsed_args.share_server:
            share_server_id = apiutils.find_resource(
                share_client.share_servers,
                parsed_args.share_server).id

        search_opts = {
            'all_projects': all_projects,
            'is_public': parsed_args.public,
            'metadata': utils.extract_key_value_options(
                parsed_args.property),
            'extra_specs': utils.extract_key_value_options(
                parsed_args.extra_spec),
            'limit': parsed_args.limit,
            'name': parsed_args.name,
            'status': parsed_args.status,
            'host': parsed_args.host,
            'share_server_id': share_server_id,
            'share_network_id': share_network_id,
            'share_type_id': share_type_id,
            'snapshot_id': snapshot_id,
            'share_group_id': share_group_id,
            'project_id': project_id,
            'user_id': user_id,
            'offset': parsed_args.marker,
            'limit': parsed_args.limit,
        }

        # NOTE(vkmc) We implemented sorting and filtering in manilaclient
        # but we will use the one provided by osc
        data = share_client.shares.list(search_opts=search_opts)
        data = oscutils.sort_items(data, parsed_args.sort, str)

        return (column_headers, (oscutils.get_item_properties
                (s, columns, formatters={'Metadata': oscutils.format_dict},)
                for s in data))


class ShowShare(command.ShowOne):
    """Show a share."""
    _description = _("Display share details")

    def get_parser(self, prog_name):
        parser = super(ShowShare, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Share to display (name or ID)')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_obj = apiutils.find_resource(share_client.shares,
                                           parsed_args.share)

        export_locations = share_client.share_export_locations.list(share_obj)
        export_locations = (
            cliutils.transform_export_locations_to_string_view(
                export_locations))

        data = share_obj._info
        data['export_locations'] = export_locations
        # Special mapping for columns to make the output easier to read:
        # 'metadata' --> 'properties'
        data.update(
            {
                'properties':
                format_columns.DictColumn(data.pop('metadata', {})),
            },
        )

        # Remove key links from being displayed
        data.pop("links", None)
        data.pop("shares_type", None)

        return self.dict2columns(data)
