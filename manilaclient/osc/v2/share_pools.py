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
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as osc_utils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.osc import utils


class ListSharePools(command.Lister):
    """List all backend storage pools known to the scheduler (Admin only)."""
    _description = _(
        "List all backend storage pools known to the scheduler (Admin only).")

    def get_parser(self, prog_name):
        parser = super(ListSharePools, self).get_parser(prog_name)
        parser.add_argument(
            "--host",
            metavar="<host>",
            default=None,
            help=_("Filter results by host name. "
                   "Regular expressions are supported.")
        )
        parser.add_argument(
            "--backend",
            metavar="<backend>",
            default=None,
            help=_("Filter results by backend name. "
                   "Regular expressions are supported.")
        )
        parser.add_argument(
            "--pool",
            metavar="<pool>",
            default=None,
            help=_("Filter results by pool name. "
                   "Regular expressions are supported.")
        )
        parser.add_argument(
            "--detail",
            action='store_true',
            default=False,
            help=_("Show detailed information about pools.")
        )
        parser.add_argument(
            "--share-type",
            metavar="<share-type>",
            default=None,
            help=_("Filter results by share type name or ID. "
                   "Available only for microversion >= 2.23")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = None
        if parsed_args.share_type:
            if share_client.api_version >= api_versions.APIVersion("2.23"):
                share_type = osc_utils.find_resource(
                    share_client.share_types,
                    parsed_args.share_type).id
            else:
                raise exceptions.CommandError(_(
                    "Filtering results by share type is only available with "
                    "manila API version >= 2.23"))

        search_opts = {
            'host': parsed_args.host,
            'backend': parsed_args.backend,
            'pool': parsed_args.pool,
            'share_type': share_type,
        }

        pools = share_client.pools.list(
            detailed=parsed_args.detail, search_opts=search_opts)

        columns = ["Name", "Host", "Backend", "Pool"]

        if parsed_args.detail:
            columns.append("Capabilities")
            if parsed_args.formatter == 'table':
                for pool in pools:
                    pool._info.update({
                        'capabilities': utils.format_properties(
                            pool.capabilities)})

        data = (osc_utils.get_dict_properties(
            pool._info, columns) for pool in pools)

        return (columns, data)
