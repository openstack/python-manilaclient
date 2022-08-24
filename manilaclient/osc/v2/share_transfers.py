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

import logging

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import constants


LOG = logging.getLogger(__name__)

TRANSFER_DETAIL_ATTRIBUTES = [
    'id',
    'created_at',
    'name',
    'resource_type',
    'resource_id',
    'source_project_id',
    'destination_project_id',
    'accepted',
    'expires_at'
]

TRANSFER_SUMMARY_ATTRIBUTES = [
    'id',
    'name',
    'resource_type',
    'resource_id',
]


class CreateShareTransfer(command.ShowOne):
    """Create a new share transfer."""
    _description = _("Create a new share transfer")

    def get_parser(self, prog_name):
        parser = super(CreateShareTransfer, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar='<share>',
            help='Name or ID of share to transfer.')
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help='Transfer name. Default=None.')
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = osc_utils.find_resource(share_client.shares,
                                        parsed_args.share)
        transfer = share_client.transfers.create(
            share.id, name=parsed_args.name)

        transfer._info.pop('links', None)

        return self.dict2columns(transfer._info)


class DeleteShareTransfer(command.Command):
    """Remove one or more transfers."""
    _description = _("Remove one or more transfers")

    def get_parser(self, prog_name):
        parser = super(DeleteShareTransfer, self).get_parser(prog_name)
        parser.add_argument(
            'transfer',
            metavar='<transfer>',
            nargs='+',
            help='Name(s) or ID(s) of the transfer(s).')
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        failure_count = 0

        for transfer in parsed_args.transfer:
            try:
                transfer_obj = apiutils.find_resource(
                    share_client.transfers,
                    transfer)
                share_client.transfers.delete(transfer_obj.id)
            except Exception as e:
                failure_count += 1
                LOG.error(_(
                    "Failed to delete %(transfer)s: %(e)s"),
                    {'transfer': transfer, 'e': e})

        if failure_count > 0:
            raise exceptions.CommandError(_(
                "Unable to delete some or all of the specified transfers."))


class ListShareTransfer(command.Lister):
    """Lists all transfers."""
    _description = _("Lists all transfers")

    def get_parser(self, prog_name):
        parser = super(ListShareTransfer, self).get_parser(prog_name)
        parser.add_argument(
            '--all-projects',
            action='store_true',
            help=_("Shows details for all tenants. (Admin only).")
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help='Filter share transfers by name. Default=None.')
        parser.add_argument(
            '--id',
            metavar='<id>',
            default=None,
            help='Filter share transfers by ID. Default=None.')
        parser.add_argument(
            '--resource-type', '--resource_type',
            metavar='<resource_type>',
            default=None,
            help='Filter share transfers by resource type, '
                 'which can be share. Default=None.')
        parser.add_argument(
            '--resource-id', '--resource_id',
            metavar='<resource_id>',
            default=None,
            help='Filter share transfers by resource ID. Default=None.')
        parser.add_argument(
            '--source-project-id', '--source_project_id',
            metavar='<source_project_id>',
            default=None,
            help='Filter share transfers by ID of the Project that '
                 'initiated the transfer. Default=None.')
        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            default=None,
            help='Maximum number of transfer records to '
                 'return. (Default=None)')
        parser.add_argument(
            '--offset',
            metavar="<offset>",
            default=None,
            help='Start position of transfer records listing.')
        parser.add_argument(
            '--sort-key', '--sort_key',
            metavar='<sort_key>',
            type=str,
            default=None,
            help='Key to be sorted, available keys are %(keys)s. '
                 'Default=None.'
                 % {'keys': constants.SHARE_TRANSFER_SORT_KEY_VALUES})
        parser.add_argument(
            '--sort-dir', '--sort_dir',
            metavar='<sort_dir>',
            type=str,
            default=None,
            help='Sort direction, available values are %(values)s. '
                 'OPTIONAL: Default=None.' % {
                     'values': constants.SORT_DIR_VALUES})
        parser.add_argument(
            '--detailed',
            dest='detailed',
            metavar='<0|1>',
            nargs='?',
            type=int,
            const=1,
            default=0,
            help="Show detailed information about filtered share transfers.")
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        columns = [
            'ID',
            'Name',
            'Resource Type',
            'Resource Id'
        ]

        if parsed_args.detailed:
            columns.extend(['Created At', 'Source Project Id',
                            'Destination Project Id', 'Accepted',
                            'Expires At'])

        search_opts = {
            'all_tenants': parsed_args.all_projects,
            'id': parsed_args.id,
            'name': parsed_args.name,
            'limit': parsed_args.limit,
            'offset': parsed_args.offset,
            'resource_type': parsed_args.resource_type,
            'resource_id': parsed_args.resource_id,
            'source_project_id': parsed_args.source_project_id,
        }

        transfers = share_client.transfers.list(
            detailed=parsed_args.detailed, search_opts=search_opts,
            sort_key=parsed_args.sort_key, sort_dir=parsed_args.sort_dir)

        return (columns, (osc_utils.get_item_properties
                (m, columns) for m in transfers))


class ShowShareTransfer(command.ShowOne):
    """Show details about a share transfer."""
    _description = _("Show details about a share transfer")

    def get_parser(self, prog_name):
        parser = super(ShowShareTransfer, self).get_parser(prog_name)
        parser.add_argument(
            'transfer',
            metavar='<transfer>',
            help=_('Name or ID of transfer to show.'))
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        transfer = apiutils.find_resource(
            share_client.transfers,
            parsed_args.transfer)

        return (TRANSFER_DETAIL_ATTRIBUTES, osc_utils.get_dict_properties(
            transfer._info, TRANSFER_DETAIL_ATTRIBUTES))


class AcceptShareTransfer(command.Command):
    """Accepts a share transfer."""
    _description = _("Accepts a share transfer")

    def get_parser(self, prog_name):
        parser = super(AcceptShareTransfer, self).get_parser(prog_name)
        parser.add_argument(
            'transfer',
            metavar='<transfer>',
            help='ID of transfer to accept.')
        parser.add_argument(
            'auth_key',
            metavar='<auth_key>',
            help='Authentication key of transfer to accept.')
        parser.add_argument(
            '--clear-rules',
            '--clear_rules',
            dest='clear_rules',
            action='store_true',
            default=False,
            help="Whether manila should clean up the access rules after the "
                 "transfer is complete. (Default=False)")
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_client.transfers.accept(
            parsed_args.transfer, parsed_args.auth_key,
            clear_access_rules=parsed_args.clear_rules)
