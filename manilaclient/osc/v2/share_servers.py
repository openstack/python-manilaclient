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
from osc_lib.cli import parseractions
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import constants

LOG = logging.getLogger(__name__)


class DeleteShareServer(command.Command):
    """Delete one or more share servers (Admin only)"""
    _description = _(
        "Delete one or more share servers")

    def get_parser(self, prog_name):
        parser = super(DeleteShareServer, self).get_parser(prog_name)
        parser.add_argument(
            "share_servers",
            metavar="<share-server>",
            nargs="+",
            help=_("ID(s) of the server(s) to delete")
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share server deletion.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for server in parsed_args.share_servers:
            try:
                server_obj = osc_utils.find_resource(
                    share_client.share_servers, server)

                share_client.share_servers.delete(server_obj)
                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                            manager=share_client.share_servers,
                            res_id=server_obj.id):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to delete a share server with "
                    "ID '%(server)s': %(e)s"),
                    {'server': server, 'e': e})

        if result > 0:
            total = len(parsed_args.share_servers)
            msg = f'Failed to delete {result} servers out of {total}.'
            raise exceptions.CommandError(_(msg))


class ShowShareServer(command.ShowOne):
    """Show share server (Admin only)."""
    _description = _("Show details about a share server (Admin only).")

    def get_parser(self, prog_name):
        parser = super(ShowShareServer, self).get_parser(prog_name)
        parser.add_argument(
            "share_server",
            metavar="<share-server>",
            help=_("ID of share server.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_server = osc_utils.find_resource(
            share_client.share_servers,
            parsed_args.share_server)

        # All 'backend_details' data already present as separated strings,
        # so remove big dict from view.
        if "backend_details" in share_server._info:
            del share_server._info["backend_details"]

        share_server._info.pop('links', None)
        return self.dict2columns(share_server._info)


class ListShareServer(command.Lister):
    """List all share servers (Admin only)."""
    _description = _("List all share servers (Admin only).")

    def get_parser(self, prog_name):
        parser = super(ListShareServer, self).get_parser(prog_name)
        parser.add_argument(
            '--host',
            metavar='<hostname>',
            default=None,
            help=_('Filter results by name of host.'),
        )
        parser.add_argument(
            '--status',
            metavar="<status>",
            default=None,
            help=_('Filter results by status.')
        )
        parser.add_argument(
            '--share-network',
            metavar='<share-network>',
            default=None,
            help=_('Filter results by share network name or ID.'),
        )
        parser.add_argument(
            '--project',
            metavar='<project>',
            default=None,
            help=_('Filter results by project name or ID.')
        )
        parser.add_argument(
            '--share-network-subnet',
            metavar='<share-network-subnet>',
            type=str,
            default=None,
            help=_("Filter results by share network subnet that the "
                   "share server's network allocation exists within. "
                   "Available for microversion >= 2.51 (Optional, "
                   "Default=None)")
        )
        identity_common.add_project_domain_option_to_parser(parser)
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        project_id = None
        if parsed_args.project:
            project_id = identity_common.find_project(
                identity_client,
                parsed_args.project,
                parsed_args.project_domain).id

        if (parsed_args.share_network_subnet and
                share_client.api_version < api_versions.APIVersion("2.51")):
            raise exceptions.CommandError(
                "Share network subnet can be specified only with manila API "
                "version >= 2.51"
            )

        columns = [
            'ID',
            'Host',
            'Status',
            'Share Network ID',
            'Project ID',
        ]

        search_opts = {
            'status': parsed_args.status,
            'host': parsed_args.host,
            'project_id': project_id,
        }

        if parsed_args.share_network:
            share_network_id = osc_utils.find_resource(
                share_client.share_networks,
                parsed_args.share_network).id
            search_opts['share_network'] = share_network_id

        if parsed_args.share_network_subnet:
            search_opts['share_network_subnet_id'] = (
                parsed_args.share_network_subnet)

        share_servers = share_client.share_servers.list(
            search_opts=search_opts)

        data = (osc_utils.get_dict_properties(
            share_server._info, columns) for share_server in share_servers)

        return (columns, data)


class AdoptShareServer(command.ShowOne):
    """Adopt share server not handled by Manila (Admin only)."""

    _description = _("Adopt share server not handled by Manila (Admin only).")

    def get_parser(self, prog_name):
        parser = super(AdoptShareServer, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            type=str,
            help=_('Backend name as "<node_hostname>@<backend_name>".')
        )
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Share network where share server has network "
                   "allocations in.")
        )
        parser.add_argument(
            'identifier',
            metavar='<identifier>',
            type=str,
            help=_("A driver-specific share server identifier required "
                   "by the driver to manage the share server.")
        )
        parser.add_argument(
            '--driver-options',
            metavar='<key=value>',
            action=parseractions.KeyValueAction,
            default={},
            help=_("One or more driver-specific key=value pairs that may be "
                   "necessary to manage the share server (Optional, "
                   "Default=None).")
        )
        parser.add_argument(
            '--share-network-subnet',
            type=str,
            metavar='<share-network-subnet>',
            default=None,
            help="Share network subnet where share server has network  "
                 "allocations in.The default subnet will be used if "
                 "it's not specified. Available for microversion "
                 ">= 2.51 (Optional, Default=None)."
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            help=_("Wait until share server is adopted")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_network = None
        if parsed_args.share_network:
            share_network = osc_utils.find_resource(
                share_client.share_networks,
                parsed_args.share_network).id

        share_network_subnet = None
        if (parsed_args.share_network_subnet and
                share_client.api_version < api_versions.APIVersion("2.51")):
            raise exceptions.CommandError(
                "Share network subnet can be specified only with manila API "
                "version >= 2.51"
            )
        elif parsed_args.share_network_subnet:
            share_network_subnet = share_client.share_network_subnets.get(
                share_network, parsed_args.share_network_subnet).id

        share_server = share_client.share_servers.manage(
            host=parsed_args.host,
            share_network_id=share_network,
            identifier=parsed_args.identifier,
            driver_options=parsed_args.driver_options,
            share_network_subnet_id=share_network_subnet
        )

        if parsed_args.wait:
            if not osc_utils.wait_for_status(
                status_f=share_client.share_servers.get,
                res_id=share_server.id,
                success_status=['active'],
                error_status=['manage_error', 'error']
            ):
                LOG.error(_("ERROR: Share server is in error state."))

            share_server = osc_utils.find_resource(share_client.share_servers,
                                                   share_server.id)

        share_server._info.pop('links', None)

        # All 'backend_details' data already present as separated strings,
        # so remove big dict from view.
        share_server._info.pop("backend_details", None)

        return self.dict2columns(share_server._info)


class AbandonShareServer(command.Command):
    """Remove one or more share servers (Admin only)."""

    _description = _("Remove one or more share server(s) (Admin only).")

    def get_parser(self, prog_name):
        parser = super(AbandonShareServer, self).get_parser(prog_name)
        parser.add_argument(
            "share_server",
            metavar="<share-server>",
            nargs='+',
            help=_("ID of the server(s) to be abandoned.")
        )
        parser.add_argument(
            "--force",
            action='store_true',
            default=False,
            help=_("Enforces the unmanage share server operation, even "
                   "if the backend driver does not support it.")
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait until share server is abandoned")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for server in parsed_args.share_server:
            try:
                server_obj = osc_utils.find_resource(
                    share_client.share_servers,
                    server)
                kwargs = {}
                if parsed_args.force:
                    kwargs['force'] = parsed_args.force
                share_client.share_servers.unmanage(
                    server_obj, **kwargs)

                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                            manager=share_client.share_servers,
                            res_id=server_obj.id):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to abandon share server with "
                    "ID '%(server)s': %(e)s"),
                    {'server': server, 'e': e})

        if result > 0:
            total = len(parsed_args.share_server)
            msg = f'Failed to abandon {result} of {total} servers.'
            raise exceptions.CommandError(_(msg))


class SetShareServer(command.Command):
    """Set share server properties."""

    _description = _("Set share server properties (Admin only).")

    def get_parser(self, prog_name):
        parser = super(SetShareServer, self).get_parser(prog_name)
        allowed_update_choices = [
            'unmanage_starting', 'server_migrating_to', 'error',
            'unmanage_error', 'manage_error', 'inactive', 'active',
            'server_migrating', 'manage_starting', 'deleting',
            'network_change']
        allowed_update_choices_str = ', '.join(allowed_update_choices)
        parser.add_argument(
            "share_server",
            metavar="<share-server>",
            help=_("ID of the share server to modify.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            required=False,
            default=constants.STATUS_ACTIVE,
            help=_("Assign a status to the share server. Options "
                   "include: %s. If no state is "
                   "provided, active will be "
                   "used." % allowed_update_choices_str)
        )
        parser.add_argument(
            '--task-state',
            metavar="<task-state>",
            required=False,
            default=None,
            help=_("Indicate which task state to assign the share server. "
                   "Options include migration_starting, migration_in_progress,"
                   " migration_completing, migration_success, migration_error,"
                   " migration_cancelled, migration_driver_in_progress, "
                   "migration_driver_phase1_done, data_copying_starting, "
                   "data_copying_in_progress, data_copying_completing, "
                   "data_copying_completed, data_copying_cancelled, "
                   "data_copying_error. ")
        )
        return parser

    def take_action(self, parsed_args):
        if not parsed_args.status and not parsed_args.task_state:
            msg = (_("A status or a task state should be provided for this "
                     "command."))
            LOG.error(msg)
            raise exceptions.CommandError(msg)
        share_client = self.app.client_manager.share

        share_server = osc_utils.find_resource(
            share_client.share_servers,
            parsed_args.share_server)

        if parsed_args.status:
            try:
                share_client.share_servers.reset_state(
                    share_server,
                    parsed_args.status
                )
            except Exception as e:
                msg = (_(
                    "Failed to set status '%(status)s': %(exception)s"),
                    {'status': parsed_args.status, 'exception': e})
                LOG.error(msg)
                raise exceptions.CommandError(msg)

        if parsed_args.task_state:
            if share_client.api_version < api_versions.APIVersion("2.57"):
                raise exceptions.CommandError(
                    "Setting the state of a share server is only available "
                    "with manila API version >= 2.57")
            else:
                result = 0
                try:
                    share_client.share_servers.reset_task_state(
                        share_server, parsed_args.task_state)
                except Exception as e:
                    LOG.error(_("Failed to update share server task state "
                                "%s"), e)
                    result += 1

            if result > 0:
                raise exceptions.CommandError(_("One or more of the "
                                              "reset operations failed"))


class ShareServerMigrationCancel(command.Command):
    """Attempts to cancel migration for a given share server

    :param share_server: either share_server object or text with its ID.

    """

    _description = _("Cancels migration of a given share server when copying")

    def get_parser(self, prog_name):
        parser = super(ShareServerMigrationCancel, self).get_parser(prog_name)
        parser.add_argument(
            'share_server',
            metavar='<share_server>',
            help=_('ID of share server to cancel migration.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_server = osc_utils.find_resource(
            share_client.share_servers,
            parsed_args.share_server)
        if share_client.api_version >= api_versions.APIVersion("2.57"):
            share_server.migration_cancel()
        else:
            raise exceptions.CommandError(
                "Share Server Migration cancel is only available "
                "with manila API version >= 2.57")


class ShareServerMigrationComplete(command.Command):
    """Completes migration for a given share server (Admin only, Experimental).

    """
    _description = _("Completes migration for a given share server")

    def get_parser(self, prog_name):
        parser = super(ShareServerMigrationComplete, self).get_parser(
            prog_name)
        parser.add_argument(
            'share_server',
            metavar='<share_server>',
            help=_('ID of share server to complete migration.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_server = osc_utils.find_resource(
            share_client.share_servers,
            parsed_args.share_server)
        if share_client.api_version >= api_versions.APIVersion("2.57"):
            share_server.migration_complete()
        else:
            raise exceptions.CommandError(
                "Share Server Migration complete is only available "
                "with manila API version >= 2.57")


class ShareServerMigrationShow(command.ShowOne):
    """Obtains progress of share migration for a given share server.

    (Admin only, Experimental).

    :param share_server: either share_server object or text with its ID.

    """

    _description = _(
        "Gets migration progress of a given share server when copying")

    def get_parser(self, prog_name):
        parser = super(ShareServerMigrationShow, self).get_parser(prog_name)
        parser.add_argument(
            'share_server',
            metavar='<share_server>',
            help='ID of share server to show migration progress for.'
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        if share_client.api_version >= api_versions.APIVersion("2.57"):
            share_server = osc_utils.find_resource(
                share_client.share_servers,
                parsed_args.share_server)
            result = share_server.migration_get_progress()
            return self.dict2columns(result)
        else:
            raise exceptions.CommandError(
                "Share Server Migration show is only available "
                "with manila API version >= 2.57")


class ShareServerMigrationStart(command.ShowOne):
    """Migrates share server to a new host (Admin only, Experimental)."""

    _description = _("Migrates share server to a new host.")

    def get_parser(self, prog_name):
        parser = super(ShareServerMigrationStart, self).get_parser(prog_name)
        parser.add_argument(
            'share_server',
            metavar='<share_server>',
            help=_('ID of share server to start migration.')
        )
        parser.add_argument(
            'host',
            metavar='<host@backend>',
            help=_("Destination to migrate the share server to. Use "
                   "the format '<node_hostname>@<backend_name>'.")
        )
        parser.add_argument(
            '--preserve-snapshots',
            metavar='<True|False>',
            choices=['True', 'False'],
            required=True,
            help=_("Set to True if snapshots must be preserved at "
                   "the migration destination.")
        )
        parser.add_argument(
            '--writable',
            metavar='<True|False>',
            choices=['True', 'False'],
            required=True,
            help=_("Enforces migration to keep all its shares writable "
                   "while contents are being moved.")
        )
        parser.add_argument(
            '--nondisruptive',
            metavar='<True|False>',
            choices=['True', 'False'],
            required=True,
            help=_("Enforces migration to be nondisruptive.")
        )
        parser.add_argument(
            '--new-share-network',
            metavar='<new_share_network>',
            required=False,
            default=None,
            help=_('Specify a new share network for the share server. Do not '
                   'specify this parameter if the migrating share server has '
                   'to be retained within its current share network.',)
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            default=False,
            help=_("Run a dry-run of the share server migration. ")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        share_server = osc_utils.find_resource(
            share_client.share_servers,
            parsed_args.share_server)

        if share_client.api_version >= api_versions.APIVersion("2.57"):
            new_share_net_id = None
            result = None
            if parsed_args.new_share_network:
                new_share_net_id = apiutils.find_resource(
                    share_client.share_networks,
                    parsed_args.new_share_network).id
            if parsed_args.check_only:
                result = share_server.migration_check(
                    parsed_args.host, parsed_args.writable,
                    parsed_args.nondisruptive, parsed_args.preserve_snapshots,
                    new_share_net_id
                )
            if result:
                return self.dict2columns(result)
            else:
                share_server.migration_start(parsed_args.host,
                                             parsed_args.writable,
                                             parsed_args.nondisruptive,
                                             parsed_args.preserve_snapshots,
                                             new_share_net_id)
                return ({}, {})
        else:
            raise exceptions.CommandError(
                "Share Server Migration is only available "
                "with manila API version >= 2.57")
