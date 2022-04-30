# Copyright 2023 Cloudification GmbH.
# All Rights Reserved.
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

from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _
from manilaclient.common import constants
from manilaclient.osc import utils

LOG = logging.getLogger(__name__)


class CreateShareBackup(command.ShowOne):
    """Create a share backup."""
    _description = _("Create a backup of the given share")

    def get_parser(self, prog_name):
        parser = super(CreateShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "share",
            metavar="<share>",
            help=_("Name or ID of the share to backup.")
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help=_('Optional share backup name. (Default=None).')
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_('Optional share backup description. (Default=None).')
        )
        parser.add_argument(
            "--backup-options",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_("Backup driver option key=value pairs (Optional, "
                   "Default=None)."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share = osc_utils.find_resource(
            share_client.shares, parsed_args.share)

        body = {}
        if parsed_args.backup_options:
            body['backup_options'] = utils.extract_key_value_options(
                parsed_args.backup_options)
        if parsed_args.description:
            body['description'] = parsed_args.description
        if parsed_args.name:
            body['name'] = parsed_args.name

        share_backup = share_client.share_backups.create(share, **body)
        share_backup._info.pop('links', None)
        return self.dict2columns(share_backup._info)


class DeleteShareBackup(command.Command):
    """Delete one or more share backups."""
    _description = _("Delete one or more share backups")

    def get_parser(self, prog_name):
        parser = super(DeleteShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "backup",
            metavar="<backup>",
            nargs="+",
            help=_("Name or ID of the backup(s) to delete")
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share backup deletion")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for backup in parsed_args.backup:
            try:
                share_backup_obj = osc_utils.find_resource(
                    share_client.share_backups, backup)
                share_client.share_backups.delete(share_backup_obj)

                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                            manager=share_client.share_backups,
                            res_id=share_backup_obj.id):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to delete a share backup with "
                    "name or ID '%(backup)s': %(e)s"),
                    {'backup': backup, 'e': e})

        if result > 0:
            total = len(parsed_args.backup)
            msg = (_("%(result)s of %(total)s backups failed "
                   "to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ListShareBackup(command.Lister):
    """List share backups."""
    _description = _("List share backups")

    def get_parser(self, prog_name):
        parser = super(ListShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "--share",
            metavar="<share>",
            default=None,
            help=_("Name or ID of the share to list backups for.")
        )
        parser.add_argument(
            "--name",
            metavar="<name>",
            default=None,
            help=_("Filter results by name. Default=None.")
        )
        parser.add_argument(
            '--description',
            metavar="<description>",
            default=None,
            help=_("Filter results by description. Default=None.")
        )
        parser.add_argument(
            "--name~",
            metavar="<name~>",
            default=None,
            help=_("Filter results matching a share backup name pattern. ")
        )
        parser.add_argument(
            '--description~',
            metavar="<description~>",
            default=None,
            help=_("Filter results matching a share backup description ")
        )
        parser.add_argument(
            '--status',
            metavar="<status>",
            default=None,
            help=_('Filter results by status. Default=None.')
        )
        parser.add_argument(
            "--limit",
            metavar="<num-backups>",
            type=int,
            default=None,
            action=parseractions.NonNegativeAction,
            help=_("Limit the number of backups returned. Default=None.")
        )
        parser.add_argument(
            '--offset',
            metavar="<offset>",
            default=None,
            help='Start position of backup records listing.')
        parser.add_argument(
            '--sort-key', '--sort_key',
            metavar='<sort_key>',
            type=str,
            default=None,
            help='Key to be sorted, available keys are %(keys)s. '
                 'Default=None.'
                 % {'keys': constants.BACKUP_SORT_KEY_VALUES})
        parser.add_argument(
            '--sort-dir', '--sort_dir',
            metavar='<sort_dir>',
            type=str,
            default=None,
            help='Sort direction, available values are %(values)s. '
                 'OPTIONAL: Default=None.' % {
                     'values': constants.SORT_DIR_VALUES})
        parser.add_argument(
            '--detail',
            dest='detail',
            metavar='<0|1>',
            nargs='?',
            type=int,
            const=1,
            default=0,
            help="Show detailed information about share backups.")
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_id = None
        if parsed_args.share:
            share_id = osc_utils.find_resource(share_client.shares,
                                               parsed_args.share).id
        columns = [
            'ID',
            'Name',
            'Share ID',
            'Status'
        ]

        if parsed_args.detail:
            columns.extend(['Description', 'Size', 'Created At',
                            'Updated At', 'Availability Zone', 'Progress',
                            'Restore Progress', 'Host', 'Topic'])

        search_opts = {
            'limit': parsed_args.limit,
            'offset': parsed_args.offset,
            'name': parsed_args.name,
            'description': parsed_args.description,
            'status': parsed_args.status,
            'share_id': share_id,
        }

        search_opts['name~'] = getattr(parsed_args, 'name~')
        search_opts['description~'] = getattr(parsed_args, 'description~')

        backups = share_client.share_backups.list(
            detailed=parsed_args.detail, search_opts=search_opts,
            sort_key=parsed_args.sort_key, sort_dir=parsed_args.sort_dir)

        return (columns,
                (osc_utils.get_item_properties(b, columns) for b in backups))


class ShowShareBackup(command.ShowOne):
    """Show share backup."""
    _description = _("Show details of a backup")

    def get_parser(self, prog_name):
        parser = super(ShowShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "backup",
            metavar="<backup>",
            help=_("ID of the share backup. ")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        backup = osc_utils.find_resource(share_client.share_backups,
                                         parsed_args.backup)
        backup._info.pop('links', None)
        return self.dict2columns(backup._info)


class RestoreShareBackup(command.Command):
    """Restore share backup to share"""
    _description = _("Attempt to restore share backup")

    def get_parser(self, prog_name):
        parser = super(RestoreShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "backup",
            metavar="<backup>",
            help=_('ID of backup to restore.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_backup = osc_utils.find_resource(
            share_client.share_backups,
            parsed_args.backup)
        share_client.share_backups.restore(share_backup.id)


class SetShareBackup(command.Command):
    """Set share backup properties."""
    _description = _("Set share backup properties")

    def get_parser(self, prog_name):
        parser = super(SetShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "backup",
            metavar="<backup>",
            help=_('Name or ID of the backup to set a property for')
        )
        parser.add_argument(
            "--name",
            metavar="<name>",
            default=None,
            help=_("Set a name to the backup.")
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("Set a description to the backup.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            choices=['available', 'error', 'creating', 'deleting',
                     'restoring'],
            help=_("Assign a status to the backup(Admin only). "
                   "Options include : available, error, creating, "
                   "deleting, restoring.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        share_backup = osc_utils.find_resource(
            share_client.share_backups,
            parsed_args.backup)

        kwargs = {}

        if parsed_args.name is not None:
            kwargs['name'] = parsed_args.name
        if parsed_args.description is not None:
            kwargs['description'] = parsed_args.description

        try:
            share_client.share_backups.update(share_backup, **kwargs)
        except Exception as e:
            result += 1
            LOG.error(_(
                "Failed to set share backup properties "
                "'%(properties)s': %(exception)s"),
                {'properties': kwargs,
                 'exception': e})

        if parsed_args.status:
            try:
                share_client.share_backups.reset_status(
                    share_backup,
                    parsed_args.status
                )
            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to update backup status to "
                    "'%(status)s': %(e)s"),
                    {'status': parsed_args.status, 'e': e})
        if result > 0:
            raise exceptions.CommandError(_("One or more of the "
                                          "set operations failed"))


class UnsetShareBackup(command.Command):
    """Unset share backup properties."""
    _description = _("Unset share backup properties")

    def get_parser(self, prog_name):
        parser = super(UnsetShareBackup, self).get_parser(prog_name)
        parser.add_argument(
            "backup",
            metavar="<backup>",
            help=_('Name or ID of the backup to unset a property for')
        )
        parser.add_argument(
            "--name",
            action='store_true',
            help=_("Unset a name to the backup.")
        )
        parser.add_argument(
            "--description",
            action='store_true',
            help=_("Unset a description to the backup.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_backup = osc_utils.find_resource(
            share_client.share_backups,
            parsed_args.backup)

        kwargs = {}
        if parsed_args.name:
            kwargs['name'] = None
        if parsed_args.description:
            kwargs['description'] = None
        if not kwargs:
            msg = "Either name or description must be provided."
            raise exceptions.CommandError(msg)

        try:
            share_client.share_backups.update(share_backup, **kwargs)
        except Exception as e:
            LOG.error(_(
                "Failed to unset share backup properties "
                "'%(properties)s': %(exception)s"),
                {'properties': kwargs,
                 'exception': e})
