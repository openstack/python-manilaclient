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

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common import cliutils
from manilaclient.osc import utils

LOG = logging.getLogger(__name__)


class CreateShareReplica(command.ShowOne):
    """Create a share replica."""
    _description = _("Create a replica of the given share")

    def get_parser(self, prog_name):
        parser = super(CreateShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "share",
            metavar="<share>",
            help=_("Name or ID of the share to replicate.")
        )
        parser.add_argument(
            '--availability-zone',
            metavar='<availability-zone>',
            default=None,
            help=_('Availability zone in which the replica should be created.')
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            default=False,
            help=_('Wait for replica creation')
        )
        parser.add_argument(
            "--scheduler-hint",
            metavar="<key=value>",
            default={},
            action=parseractions.KeyValueAction,
            help=_("Scheduler hint for the share replica as key=value pairs, "
                   "Supported key is only_host. Available for microversion "
                   ">= 2.67."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share = osc_utils.find_resource(share_client.shares,
                                        parsed_args.share)
        scheduler_hints = {}
        if parsed_args.scheduler_hint:
            if share_client.api_version < api_versions.APIVersion("2.67"):
                raise exceptions.CommandError(_(
                    "arg '--scheduler_hint' is available only starting with "
                    "API microversion '2.67'."))

            hints = utils.extract_key_value_options(parsed_args.scheduler_hint)
            if 'only_host' not in hints.keys() or len(hints) > 1:
                raise exceptions.CommandError(
                    "The only valid key supported with the --scheduler-hint "
                    "argument is 'only_host'.")
            scheduler_hints['only_host'] = hints.get('only_host')

        body = {
            'share': share,
            'availability_zone': parsed_args.availability_zone,
        }
        if scheduler_hints:
            body['scheduler_hints'] = scheduler_hints

        share_replica = share_client.share_replicas.create(**body)
        if parsed_args.wait:
            if not osc_utils.wait_for_status(
                status_f=share_client.share_replicas.get,
                res_id=share_replica.id,
                success_status=['available']
            ):
                LOG.error(_("ERROR: Share replica is in error state."))

            share_replica = osc_utils.find_resource(
                share_client.share_replicas,
                share_replica.id)

        return self.dict2columns(share_replica._info)


class DeleteShareReplica(command.Command):
    """Delete one or more share replicas."""
    _description = _("Delete one or more share replicas")

    def get_parser(self, prog_name):
        parser = super(DeleteShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            nargs="+",
            help=_("Name or ID of the replica(s) to delete")
        )
        parser.add_argument(
            "--force",
            action='store_true',
            default=False,
            help=_("Attempt to force delete a replica on its backend. "
                   "Using this option will purge the replica from Manila "
                   "even if it is not cleaned up on the backend. ")
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share replica deletion")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for replica in parsed_args.replica:
            try:
                replica_obj = osc_utils.find_resource(
                    share_client.share_replicas,
                    replica)

                share_client.share_replicas.delete(
                    replica_obj,
                    force=parsed_args.force)

                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                            manager=share_client.share_replicas,
                            res_id=replica_obj.id):
                        result += 1

            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to delete a share replica with "
                    "name or ID '%(replica)s': %(e)s"),
                    {'replica': replica, 'e': e})

        if result > 0:
            total = len(parsed_args.replica)
            msg = (_("%(result)s of %(total)s replicas failed "
                   "to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class ListShareReplica(command.Lister):
    """List share replicas."""
    _description = _("List share replicas")

    def get_parser(self, prog_name):
        parser = super(ListShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "--share",
            metavar="<share>",
            default=None,
            help=_("Name or ID of the share to list replicas for.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share = None
        if parsed_args.share:
            share = osc_utils.find_resource(
                share_client.shares,
                parsed_args.share)

        replicas = share_client.share_replicas.list(share=share)

        columns = [
            'id',
            'status',
            'replica_state',
            'share_id',
            'host',
            'availability_zone',
            'updated_at',
        ]

        column_headers = utils.format_column_headers(columns)
        data = (osc_utils.get_dict_properties(
            replica._info, columns) for replica in replicas)

        return (column_headers, data)


class ShowShareReplica(command.ShowOne):
    """Show share replica."""
    _description = _("Show details about a replica")

    def get_parser(self, prog_name):
        parser = super(ShowShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica. Available only for "
                   "microversion >= 2.47. ")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = share_client.share_replicas.get(
            parsed_args.replica)

        replica_export_locations = (
            share_client.share_replica_export_locations.list(
                share_replica=replica))

        replica._info['export_locations'] = []
        for element_location in replica_export_locations:
            element_location._info.pop('links', None)
            replica._info['export_locations'].append(
                element_location._info)

        if parsed_args.formatter == 'table':
            replica._info['export_locations'] = (
                cliutils.convert_dict_list_to_string(
                    replica._info['export_locations']))

        replica._info.pop('links', None)

        return self.dict2columns(replica._info)


class SetShareReplica(command.Command):
    """Set share replica"""

    _description = _("Explicitly set share replica status and/or "
                     "replica-state")

    def get_parser(self, prog_name):
        parser = super(SetShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica to modify.")
        )
        parser.add_argument(
            "--replica-state",
            metavar="<replica-state>",
            choices=['in_sync', 'out_of_sync', 'active', 'error'],
            help=_("Indicate which replica_state to assign the replica. "
                   "Options include in_sync, out_of_sync, active and error.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            choices=['available', 'error', 'creating', 'deleting',
                     'error_deleting'],
            help=_("Indicate which status to assign the replica. Options "
                   "include available, error, creating, deleting and "
                   "error_deleting.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        replica = osc_utils.find_resource(
            share_client.share_replicas,
            parsed_args.replica)

        if parsed_args.replica_state:
            try:
                share_client.share_replicas.reset_replica_state(
                    replica,
                    parsed_args.replica_state
                )
            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to set replica_state "
                    "'%(replica_state)s': %(exception)s"),
                    {'replica_state': parsed_args.replica_state,
                     'exception': e})

        if parsed_args.status:
            try:
                share_client.share_replicas.reset_state(
                    replica,
                    parsed_args.status
                )
            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to set status '%(status)s': %(exception)s"),
                    {'status': parsed_args.status, 'exception': e})

        if not parsed_args.replica_state and not parsed_args.status:
            raise exceptions.CommandError(_(
                "Nothing to set. Please define "
                "either '--replica_state' or '--status'."))
        if result > 0:
            raise exceptions.CommandError(_("One or more of the "
                                          "set operations failed"))


class PromoteShareReplica(command.Command):
    """Promote share replica"""

    _description = _("Promote specified replica to 'active' "
                     "replica_state.")

    def get_parser(self, prog_name):
        parser = super(PromoteShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_replicas,
            parsed_args.replica)

        try:
            share_client.share_replicas.promote(replica)
        except Exception as e:
            raise exceptions.CommandError(_(
                "Failed to promote replica to 'active': %s" % (e)))


class ResyncShareReplica(command.Command):
    """Resync share replica"""

    _description = _("Attempt to update the share replica with its "
                     "'active' mirror.")

    def get_parser(self, prog_name):
        parser = super(ResyncShareReplica, self).get_parser(prog_name)
        parser.add_argument(
            "replica",
            metavar="<replica>",
            help=_("ID of the share replica to resync.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        replica = osc_utils.find_resource(
            share_client.share_replicas,
            parsed_args.replica)

        try:
            share_client.share_replicas.resync(replica)
        except Exception as e:
            raise exceptions.CommandError(_(
                "Failed to resync share replica: %s" % (e)))
