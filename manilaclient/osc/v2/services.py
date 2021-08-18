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
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _


class SetShareService(command.Command):
    """Enable/disable share service (Admin only)."""
    _description = _("Enable/Disable share service (Admin only).")

    def get_parser(self, prog_name):
        parser = super(SetShareService, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help=_("Host name as 'example_host@example_backend'.")
        )
        parser.add_argument(
            'binary',
            metavar='<binary>',
            help=_("Service binary, could be 'manila-share', "
                   "'manila-scheduler' or 'manila-data'")
        )
        enable_group = parser.add_mutually_exclusive_group()
        enable_group.add_argument(
            '--enable',
            action='store_true',
            help=_('Enable share service'),
        )
        enable_group.add_argument(
            '--disable',
            action='store_true',
            help=_('Disable share service'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        if parsed_args.enable:
            try:
                share_client.services.enable(
                    parsed_args.host, parsed_args.binary)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Failed to enable service: %s" % e))

        if parsed_args.disable:
            try:
                share_client.services.disable(
                    parsed_args.host, parsed_args.binary)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Failed to disable service: %s" % e))


class ListShareService(command.Lister):
    """List share services (Admin only)."""
    _description = _("List share services (Admin only).")

    def get_parser(self, prog_name):
        parser = super(ListShareService, self).get_parser(prog_name)
        parser.add_argument(
            "--host",
            metavar="<host>",
            default=None,
            help=_("Filter services by name of the host.")
        )
        parser.add_argument(
            "--binary",
            metavar="<binary>",
            default=None,
            help=_("Filter services by the name of the service.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            default=None,
            help=_("Filter results by status.")
        )
        parser.add_argument(
            "--state",
            metavar="<state>",
            default=None,
            choices=['up', 'down'],
            help=_("Filter results by state.")
        )
        parser.add_argument(
            "--zone",
            metavar="<zone>",
            default=None,
            help=_("Filter services by their availability zone.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        search_opts = {
            'host': parsed_args.host,
            'binary': parsed_args.binary,
            'status': parsed_args.status,
            'state': parsed_args.state,
            'zone': parsed_args.zone,
        }

        services = share_client.services.list(search_opts=search_opts)

        columns = [
            'ID',
            'Binary',
            'Host',
            'Zone',
            'Status',
            'State',
            'Updated At'
        ]

        data = (osc_utils.get_dict_properties(
            service._info, columns) for service in services)

        return (columns, data)
