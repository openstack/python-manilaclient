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

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import cliutils


LOG = logging.getLogger(__name__)


class ShareInstanceDelete(command.Command):
    """Forces the deletion of the share instance."""
    _description = _("Forces the deletion of a share instance")

    def get_parser(self, prog_name):
        parser = super(ShareInstanceDelete, self).get_parser(prog_name)
        parser.add_argument(
            'instance',
            metavar="<instance>",
            nargs="+",
            help=_('ID of the share instance to delete.')
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share instance deletion.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        number_of_deletion_failures = 0

        for instance in parsed_args.instance:
            try:
                share_instance = apiutils.find_resource(
                    share_client.share_instances, instance)

                share_client.share_instances.force_delete(share_instance)

                if parsed_args.wait:
                    if not osc_utils.wait_for_delete(
                            manager=share_client.share_instances,
                            res_id=share_instance.id):
                        number_of_deletion_failures += 1

            except Exception as e:
                number_of_deletion_failures += 1
                LOG.error(_(
                    "Failed to delete a share instance with "
                    "ID '%(instance)s': %(e)s"),
                    {'instance': instance, 'e': e})
        if number_of_deletion_failures > 0:
            msg = (_("%(number_of_deletion_failures)s of "
                     "%(total_of_instances)s instances failed "
                     "to delete.") % {
                'number_of_deletion_failures': number_of_deletion_failures,
                'total_of_instances': len(parsed_args.instance)})
            raise exceptions.CommandError(msg)


class ShareInstanceList(command.Lister):
    """List share instances."""
    _description = _("List share instances")

    def get_parser(self, prog_name):
        parser = super(ShareInstanceList, self).get_parser(prog_name)
        parser.add_argument(
            "--share",
            metavar="<share>",
            default=None,
            help=_("Name or ID of the share to list instances for.")
        )
        parser.add_argument(
            "--export-location",
            metavar="<export-location>",
            default=None,
            help=_("Export location to list instances for.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        instances = []
        kwargs = {}

        if parsed_args.share:
            # Check if the share exists
            share = osc_utils.find_resource(
                share_client.shares, parsed_args.share)

            instances = share_client.shares.list_instances(share)
        else:
            if share_client.api_version < api_versions.APIVersion("2.35"):
                if parsed_args.export_location:
                    raise exceptions.CommandError(
                        "Filtering by export location is only "
                        "available with manila API version >= 2.35")
            else:
                if parsed_args.export_location:
                    kwargs['export_location'] = parsed_args.export_location
            instances = share_client.share_instances.list(**kwargs)

        columns = [
            'ID',
            'Share ID',
            'Host',
            'Status',
            'Availability Zone',
            'Share Network ID',
            'Share Server ID',
            'Share Type ID',
        ]

        data = (osc_utils.get_dict_properties(
            instance._info, columns) for instance in instances)

        return (columns, data)


class ShareInstanceSet(command.Command):
    """Set share instance"""

    _description = _("Explicitly reset share instance status")

    def get_parser(self, prog_name):
        parser = super(ShareInstanceSet, self).get_parser(prog_name)
        parser.add_argument(
            "instance",
            metavar="<instance>",
            help=_("Instance to be modified.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            help=_('Indicate which state to assign the instance. Options are: '
                   'available, error, creating, deleting,'
                   'error_deleting, migrating, migrating_to, server_migrating.'
                   )
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        instance = osc_utils.find_resource(
            share_client.share_instances,
            parsed_args.instance)

        if parsed_args.status:
            try:
                share_client.share_instances.reset_state(
                    instance,
                    parsed_args.status
                )
            except Exception as e:
                LOG.error(_(
                    "Failed to set status '%(status)s': %(exception)s"),
                    {'status': parsed_args.status, 'exception': e})
                raise exceptions.CommandError(_("Set operation failed"))

        if not instance or not parsed_args.status:
            raise exceptions.CommandError(_(
                "Nothing to set. Please define a '--status'."))


class ShareInstanceShow(command.ShowOne):
    """Show share instance."""
    _description = _("Show share instance")

    def get_parser(self, prog_name):
        parser = super(ShareInstanceShow, self).get_parser(prog_name)
        parser.add_argument(
            "instance",
            metavar="<instance>",
            help=_("ID of the share instance.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        instance = osc_utils.find_resource(
            share_client.share_instances,
            parsed_args.instance)

        export_locations = share_client.share_instance_export_locations.list(
            instance)

        instance._info['export_locations'] = []
        for export_location in export_locations:
            export_location._info.pop('links', None)
            instance._info['export_locations'].append(export_location._info)

        if parsed_args.formatter == 'table':
            instance._info['export_locations'] = (
                cliutils.convert_dict_list_to_string(
                    instance._info['export_locations']))

        instance._info.pop('links', None)

        return self.dict2columns(instance._info)
