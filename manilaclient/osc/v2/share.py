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

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common.apiclient import exceptions as apiclient_exceptions
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
            metavar='<public>',
            default=False,
            help=_('Level of visibility for share. '
                   'Defines whether other tenants are able to see it or not. '
                   '(Default = False)')
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
                   'the share. (Default=None).')
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            default=False,
            help=_('Wait for share creation')
        )
        parser.add_argument(
            "--scheduler-hint",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_("Set Scheduler hints for the share as key=value pairs, "
                   "possible keys are same_host, different_host."
                   "(repeat option to set multiple hints)"),
        )

        return parser

    def take_action(self, parsed_args):
        # TODO(s0ru): the table shows 'Field', 'Value'
        share_client = self.app.client_manager.share

        if parsed_args.share_type:
            share_type = apiutils.find_resource(share_client.share_types,
                                                parsed_args.share_type).id
        else:
            try:
                share_type = apiutils.find_resource(
                    share_client.share_types, 'default').id
            except apiclient_exceptions.CommandError:
                msg = ("There is no default share type available. You must "
                       "pick a valid share type to create a share.")
                raise exceptions.CommandError(msg)

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
            snapshot_id = snapshot.id
            size = max(size or 0, snapshot.size)

        scheduler_hints = {}
        if parsed_args.scheduler_hint:
            if share_client.api_version < api_versions.APIVersion('2.65'):
                raise exceptions.CommandError(
                    'Setting share scheduler hints for a share is '
                    'available only for API microversion >= 2.65')
            else:
                scheduler_hints = utils.extract_key_value_options(
                    parsed_args.scheduler_hint)
                same_host_hint_shares = scheduler_hints.get('same_host')
                different_host_hint_shares = scheduler_hints.get(
                    'different_host')
                if same_host_hint_shares:
                    same_host_hint_shares = [
                        apiutils.find_resource(share_client.shares, sh).id
                        for sh in same_host_hint_shares.split(',')
                    ]
                    scheduler_hints['same_host'] = (
                        ','.join(same_host_hint_shares))
                if different_host_hint_shares:
                    different_host_hint_shares = [
                        apiutils.find_resource(share_client.shares, sh).id
                        for sh in different_host_hint_shares.split(',')
                    ]
                    scheduler_hints['different_host'] = (
                        ','.join(different_host_hint_shares))

        body = {
            'share_proto': parsed_args.share_proto,
            'size': size,
            'snapshot_id': snapshot_id,
            'name': parsed_args.name,
            'description': parsed_args.description,
            'metadata': parsed_args.property,
            'share_network': share_network,
            'share_type': share_type,
            'is_public': parsed_args.public,
            'availability_zone': parsed_args.availability_zone,
            'share_group_id': share_group,
            'scheduler_hints': scheduler_hints
        }

        share = share_client.shares.create(**body)

        if parsed_args.wait:
            if not oscutils.wait_for_status(
                status_f=share_client.shares.get,
                res_id=share.id,
                success_status=['available']
            ):
                LOG.error(_("ERROR: Share is in error state."))

            share = apiutils.find_resource(share_client.shares,
                                           share.id)

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
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share deletion")
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
                if parsed_args.wait:
                    if not oscutils.wait_for_delete(
                            manager=share_client.shares,
                            res_id=share_obj.id):
                        result += 1

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
            '--export-location',
            metavar='<export-location>',
            help=_('Filter shares by export location id or path. '
                   'Available only for microversion >= 2.35'),
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
        parser.add_argument(
            "--name~",
            metavar="<name~>",
            default=None,
            help=_("Filter results matching a share name pattern. "
                   "Available only for microversion >= 2.36.")
        )
        parser.add_argument(
            '--description~',
            metavar="<description~>",
            default=None,
            help=_("Filter results matching a share description pattern."
                   "Available only for microversion >= 2.36.")
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

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

        # set value of 'all_tenants' when using project option
        all_tenants = bool(parsed_args.project) or parsed_args.all_projects

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
            'all_tenants': all_tenants,
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
        }

        if share_client.api_version >= api_versions.APIVersion("2.35"):
            search_opts['export_location'] = parsed_args.export_location
        elif (getattr(parsed_args, 'export_location')):
            raise exceptions.CommandError(
                "Filtering by export location is only "
                "available with manila API version >= 2.35")

        # NOTE(vkmc) We implemented sorting and filtering in manilaclient
        # but we will use the one provided by osc
        if share_client.api_version >= api_versions.APIVersion("2.36"):
            search_opts['name~'] = getattr(parsed_args, 'name~')
            search_opts['description~'] = getattr(parsed_args, 'description~')
        elif (getattr(parsed_args, 'name~') or
              getattr(parsed_args, 'description~')):
            raise exceptions.CommandError(
                "Pattern based filtering (name~ and description~)"
                " is only available with manila API version >= 2.36")

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
        export_locations = cliutils.convert_dict_list_to_string(
            export_locations,
            ignored_keys=['replica_state',
                          'availability_zone',
                          'share_replica_id']
        )

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


class SetShare(command.Command):
    """Set share properties."""
    _description = _("Set share properties")

    def get_parser(self, prog_name):
        parser = super(SetShare, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Share to modify (name or ID)')
        )
        # 'metadata' --> 'properties'
        parser.add_argument(
            "--property",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_("Set a property to this share "
                   "(repeat option to set multiple properties)"),
        )
        parser.add_argument(
            '--name',
            metavar="<name>",
            default=None,
            help=_('New share name. (Default=None)')
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_('New share description. (Default=None)')
        )
        parser.add_argument(
            '--public',
            metavar='<public>',
            help=_('Level of visibility for share. '
                   'Defines whether other tenants are able to see it or not. ')
        )
        parser.add_argument(
            '--status',
            metavar='<status>',
            default=None,
            help=_('Explicitly update the status of a share (Admin only). '
                   'Examples include: available, error, creating, deleting, '
                   'error_deleting.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_obj = apiutils.find_resource(share_client.shares,
                                           parsed_args.share)
        result = 0

        if parsed_args.property:
            try:
                share_client.shares.set_metadata(
                    share_obj.id, parsed_args.property)
            except Exception as e:
                LOG.error(_("Failed to set share properties "
                            "'%(properties)s': %(exception)s"),
                          {'properties': parsed_args.property,
                           'exception': e})
                result += 1

        kwargs = {}
        if parsed_args.name is not None:
            kwargs['display_name'] = parsed_args.name
        if parsed_args.description is not None:
            kwargs['display_description'] = parsed_args.description
        if parsed_args.public is not None:
            kwargs['is_public'] = parsed_args.public
        if kwargs:
            try:
                share_client.shares.update(share_obj.id, **kwargs)
            except Exception as e:
                LOG.error(_("Failed to update share display name, visibility "
                          "or display description: %s"), e)
                result += 1
        if parsed_args.status:
            try:
                share_obj.reset_state(parsed_args.status)
            except Exception as e:
                LOG.error(_(
                    "Failed to set status for the share: %s"), e)
                result += 1

        if result > 0:
            raise exceptions.CommandError(_("One or more of the "
                                          "set operations failed"))


class UnsetShare(command.Command):
    """Unset share properties."""
    _description = _("Unset share properties")

    def get_parser(self, prog_name):
        parser = super(UnsetShare, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Share to modify (name or ID)')
        )
        # 'metadata' --> 'properties'
        parser.add_argument(
            '--property',
            metavar='<key>',
            action='append',
            help=_('Remove a property from share '
                   '(repeat option to remove multiple properties)'),
        )
        parser.add_argument(
            '--name',
            action='store_true',
            help=_('Unset share name.')
        )
        parser.add_argument(
            '--description',
            action='store_true',
            help=_('Unset share description.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_obj = apiutils.find_resource(share_client.shares,
                                           parsed_args.share)
        result = 0
        kwargs = {}
        if parsed_args.name:
            kwargs['display_name'] = None
        if parsed_args.description:
            kwargs['display_description'] = None
        if kwargs:
            try:
                share_client.shares.update(share_obj.id, **kwargs)
            except Exception as e:
                LOG.error(_("Failed to unset share display name "
                            "or display description: %s"), e)
                result += 1

        if parsed_args.property:
            for key in parsed_args.property:
                try:
                    share_client.shares.delete_metadata(
                        share_obj.id, [key])
                except Exception as e:
                    LOG.error(_("Failed to unset share property "
                                "'%(key)s': %(e)s"),
                              {'key': key, 'e': e})
                    result += 1

        if result > 0:
            raise exceptions.CommandError(_(
                "One or more of the "
                "unset operations failed"))


class ResizeShare(command.Command):
    """Resize a share"""
    _description = _("Resize a share")

    def get_parser(self, prog_name):
        parser = super(ResizeShare, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share to resize')
        )
        parser.add_argument(
            'new_size',
            metavar="<new-size>",
            type=int,
            help=_('New size of share, in GiBs')
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            default=False,
            help=_('Wait for share resize')
        )
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help=_('Only applicable when increasing the size of the '
                   'share，only available with microversion '
                   '2.64 and higher. (admin only)')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        share_size = share._info['size']
        new_size = parsed_args.new_size

        if share_size > new_size:
            try:
                share_client.shares.shrink(share, new_size)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Share resize failed: %s" % e
                ))
        elif share_size < new_size:
            force = False
            if parsed_args.force:
                if share_client.api_version < api_versions.APIVersion("2.64"):
                    raise exceptions.CommandError(
                        'args force is available only for '
                        'API microversion >= 2.64')
                force = True
            try:
                if force:
                    share_client.shares.extend(share, new_size, force=force)
                else:
                    share_client.shares.extend(share, new_size)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Share resize failed: %s" % e
                ))
        else:
            raise exceptions.CommandError(_(
                "Share size is already at %s GiBs" % new_size
            ))
        if parsed_args.wait:
            if not oscutils.wait_for_status(
                status_f=share_client.shares.get,
                res_id=share.id,
                success_status=['available']
            ):
                raise exceptions.CommandError(_(
                    "Share not available after resize attempt."))


class AdoptShare(command.ShowOne):
    """Adopt share not handled by Manila (Admin only)."""
    _description = _("Adopt a share")

    def get_parser(self, prog_name):
        parser = super(AdoptShare, self).get_parser(prog_name)
        parser.add_argument(
            'service_host',
            metavar="<service-host>",
            help=_('Service host: some.host@driver#pool.')
        )
        parser.add_argument(
            'protocol',
            metavar="<protocol>",
            help=_(
                'Protocol of the share to manage, such as NFS or CIFS.')
        )
        parser.add_argument(
            'export_path',
            metavar="<export-path>",
            help=_('Share export path, NFS share such as: '
                   '10.0.0.1:/example_path, CIFS share such as: '
                   '\\\\10.0.0.1\\example_cifs_share.')
        )
        parser.add_argument(
            '--name',
            metavar="<name>",
            default=None,
            help=_('Optional share name. (Default=None)')
        )
        parser.add_argument(
            '--description',
            metavar="<description>",
            default=None,
            help=_('Optional share description. (Default=None)')
        )
        parser.add_argument(
            '--share-type',
            metavar="<share-type>",
            default=None,
            help=_(
                'Optional share type assigned to share. (Default=None)')
        )
        parser.add_argument(
            '--driver-options',
            type=str,
            nargs='*',
            metavar='<key=value>',
            default=None,
            help=_(
                'Optional driver options as key=value pairs (Default=None).')
        )
        parser.add_argument(
            '--public',
            action='store_true',
            help=_('Level of visibility for share. Defines whether other '
                   'projects are able to see it or not. Available only for '
                   'microversion >= 2.8. (Default=False)')
        )
        parser.add_argument(
            '--share-server-id',
            metavar="<share-server-id>",
            help=_('Share server associated with share when using a share '
                   'type with "driver_handles_share_servers" extra_spec '
                   'set to True. Available only for microversion >= 2.49. '
                   '(Default=None)')
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            help=_("Wait until share is adopted")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        kwargs = {
            'service_host': parsed_args.service_host,
            'protocol': parsed_args.protocol,
            'export_path': parsed_args.export_path,
            'name': parsed_args.name,
            'description': parsed_args.description
        }

        share_type = None
        if parsed_args.share_type:
            share_type = apiutils.find_resource(share_client.share_types,
                                                parsed_args.share_type).id
            kwargs['share_type'] = share_type

        driver_options = None
        if parsed_args.driver_options:
            driver_options = utils.extract_properties(
                parsed_args.driver_options)
            kwargs['driver_options'] = driver_options

        if parsed_args.public:
            if share_client.api_version >= api_versions.APIVersion("2.8"):
                kwargs['public'] = True
            else:
                raise exceptions.CommandError(
                    'Setting share visibility while adopting a share is '
                    'available only for API microversion >= 2.8')

        if parsed_args.share_server_id:
            if share_client.api_version >= api_versions.APIVersion("2.49"):
                kwargs['share_server_id'] = parsed_args.share_server_id
            else:
                raise exceptions.CommandError(
                    'Selecting a share server ID is available only for '
                    'API microversion >= 2.49')

        share = share_client.shares.manage(**kwargs)

        if parsed_args.wait:
            if not oscutils.wait_for_status(
                status_f=share_client.shares.get,
                res_id=share.id,
                success_status=['available'],
                error_status=['manage_error', 'error']
            ):
                LOG.error(_("ERROR: Share is in error state."))

            share = apiutils.find_resource(share_client.shares,
                                           share.id)
        share._info.pop('links', None)

        return self.dict2columns(share._info)


class AbandonShare(command.Command):
    """Abandon a share (Admin only)."""
    _description = _("Abandon a share")

    def get_parser(self, prog_name):
        parser = super(AbandonShare, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            nargs="+",
            help=_('Name or ID of the share(s)')
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            help=_("Wait until share is abandoned")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for share in parsed_args.share:
            try:
                share_obj = apiutils.find_resource(
                    share_client.shares, share
                )
                share_client.shares.unmanage(share_obj)

                if parsed_args.wait:
                    # 'wait_for_delete' checks that the resource is no longer
                    # retrievable with the given 'res_id' so we can use it
                    # to check that the share has been abandoned
                    if not oscutils.wait_for_delete(
                            manager=share_client.shares,
                            res_id=share_obj.id):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(_("Failed to abandon share with "
                            "name or ID '%(share)s': %(e)s"),
                          {'share': share, 'e': e})

        if result > 0:
            total = len(parsed_args.share)
            msg = (_("Failed to abandon %(result)s out of %(total)s shares.")
                   % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ShareExportLocationShow(command.ShowOne):
    """Show export location of a share."""

    _description = _("Show export location of a share")

    def get_parser(self, prog_name):
        parser = super(ShareExportLocationShow, self).get_parser(
            prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share')
        )
        parser.add_argument(
            'export_location',
            metavar="<export-location>",
            help=_('ID of the share export location')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)

        export_location = share_client.share_export_locations.get(
            share=share,
            export_location=parsed_args.export_location
        )

        return self.dict2columns(export_location._info)


class ShareExportLocationList(command.Lister):
    """List export locations of a share."""

    _description = _("List export location of a share")

    def get_parser(self, prog_name):
        parser = super(ShareExportLocationList, self).get_parser(
            prog_name)

        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)

        export_locations = share_client.share_export_locations.list(
            share=share
        )

        list_of_keys = [
            'ID',
            'Path',
            'Preferred'
        ]

        return (list_of_keys, (oscutils.get_item_properties
                (s, list_of_keys) for s in export_locations))


class ShowShareProperties(command.ShowOne):
    """Show properties of a share"""
    _description = _("Show share properties")

    def get_parser(self, prog_name):
        parser = super(ShowShareProperties, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(
            share_client.shares, parsed_args.share)
        share_properties = share_client.shares.get_metadata(share)

        return self.dict2columns(share_properties._info)


class RevertShare(command.Command):
    """Revert a share to snapshot."""

    _description = _("Revert a share to the specified snapshot.")

    def get_parser(self, prog_name):
        parser = super(RevertShare, self).get_parser(prog_name)
        parser.add_argument(
            'snapshot',
            metavar="<snapshot>",
            help=_('Name or ID of the snapshot to restore. The snapshot '
                   'must be the most recent one known to manila.')
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            default=False,
            help=_('Wait for share revert')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        snapshot = apiutils.find_resource(share_client.share_snapshots,
                                          parsed_args.snapshot)
        share = apiutils.find_resource(share_client.shares,
                                       snapshot.share_id)
        try:
            share.revert_to_snapshot(snapshot)
        except Exception as e:
            raise exceptions.CommandError(_(
                "Failed to revert share to snapshot: %s" % (e)))
        if parsed_args.wait:
            if not oscutils.wait_for_status(
                status_f=share_client.shares.get,
                res_id=share.id,
                success_status=['available']
            ):
                raise exceptions.CommandError(_(
                    "Share not available after revert attempt."))


class ShareMigrationStart(command.Command):
    """Migrates share to a new host (Admin only, Experimental)."""
    _description = _("Migrates share to a new host.")

    def get_parser(self, prog_name):
        parser = super(ShareMigrationStart, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share to migrate.')
        )
        parser.add_argument(
            'host',
            metavar="<host>",
            help=_("Destination host where share will be migrated to. Use the "
                   "format 'host@backend#pool'.")
        )
        parser.add_argument(
            '--force-host-assisted-migration',
            metavar="<force-host-assisted-migration>",
            choices=['True', 'False'],
            default=False,
            help=_("Enforces the use of the host-assisted migration approach, "
                   "which bypasses driver optimizations. Default=False.")
        )
        parser.add_argument(
            '--preserve-metadata',
            metavar="<preserve-metadata>",
            required=True,
            choices=['True', 'False'],
            help=_("Enforces migration to preserve all file metadata when "
                   "moving its contents. If set to True, host-assisted"
                   "migration will not be attempted.")
        )
        parser.add_argument(
            '--preserve-snapshots',
            metavar="<preserve-snapshots>",
            required=True,
            choices=['True', 'False'],
            help=_("Enforces migration of the share snapshots to the "
                   "destination. If set to True, host-assisted migration"
                   "will not be attempted.")
        )
        parser.add_argument(
            '--writable',
            metavar="<writable>",
            required=True,
            choices=['True', 'False'],
            help=_("Enforces migration to keep the share writable while "
                   "contents are being moved. If set to True, host-assisted"
                   "migration will not be attempted.")
        )
        parser.add_argument(
            '--nondisruptive',
            metavar="<nondisruptive>",
            choices=['True', 'False'],
            required=True,
            help=_("Enforces migration to be nondisruptive. If set to True, "
                   "host-assisted migration will not be attempted.")
        )
        parser.add_argument(
            '--new-share-network',
            metavar="<new_share_network>",
            default=None,
            help=_("Specify the new share network for the share. Do not "
                   "specify this parameter if the migrating share has to be"
                   "retained within its current share network.")
        )
        parser.add_argument(
            '--new-share-type',
            metavar="<new-share-type>",
            default=None,
            help=_("Specify the new share type for the share. Do not specify "
                   "this parameter if the migrating share has to be retained "
                   "with its current share type.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        new_share_net_id = None
        if parsed_args.new_share_network:
            new_share_net_id = apiutils.find_resource(
                share_client.share_networks,
                parsed_args.new_share_network).id
        new_share_type_id = None
        if parsed_args.new_share_type:
            new_share_type_id = apiutils.find_resource(
                share_client.share_types,
                parsed_args.new_share_type).id
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        share.migration_start(parsed_args.host,
                              parsed_args.force_host_assisted_migration,
                              parsed_args.preserve_metadata,
                              parsed_args.writable,
                              parsed_args.nondisruptive,
                              parsed_args.preserve_snapshots,
                              new_share_net_id, new_share_type_id)


class ShareMigrationCancel(command.Command):
    """Cancels migration of a given share when copying

    (Admin only, Experimental).

    """
    _description = _("Cancels migration of a given share when copying")

    def get_parser(self, prog_name):
        parser = super(ShareMigrationCancel, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share to migrate.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        share.migration_cancel()


class ShareMigrationComplete(command.Command):
    """Completes migration for a given share (Admin only, Experimental)."""
    _description = _("Completes migration for a given share")

    def get_parser(self, prog_name):
        parser = super(ShareMigrationComplete, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of share to migrate.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        share.migration_complete()
