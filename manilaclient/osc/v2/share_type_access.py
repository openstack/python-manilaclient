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
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils


class ShareTypeAccessAllow(command.Command):
    """Add access for share type."""
    _description = _("Add access for share type")

    def get_parser(self, prog_name):
        parser = super(ShareTypeAccessAllow, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Share type name or ID to add access to")
        )
        parser.add_argument(
            'project_id',
            metavar="<project_id>",
            help=_("Project ID to add share type access for")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types, parsed_args.share_type)

        try:
            share_client.share_type_access.add_project_access(
                share_type,
                parsed_args.project_id)

        except Exception as e:
            raise exceptions.CommandError(
                "Failed to add access to share type : %s" % e)


class ListShareTypeAccess(command.Lister):
    """Get access list for share type."""
    _description = _("Get access list for share type")

    def get_parser(self, prog_name):
        parser = super(ListShareTypeAccess, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Share type name or ID to get access list for")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types, parsed_args.share_type)

        if share_type._info.get('share_type_access:is_public'):
            raise exceptions.CommandError(
                'Forbidden to get access list for public share type.')

        data = share_client.share_type_access.list(share_type)

        columns = ['Project ID']
        values = (oscutils.get_item_properties(s, columns) for s in data)

        return (columns, values)


class ShareTypeAccessDeny(command.Command):
    """Delete access from share type."""
    _description = _("Delete access from share type")

    def get_parser(self, prog_name):
        parser = super(ShareTypeAccessDeny, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Share type name or ID to delete access from")
        )
        parser.add_argument(
            'project_id',
            metavar="<project_id>",
            help=_("Project ID to delete share type access for")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types, parsed_args.share_type)

        try:
            share_client.share_type_access.remove_project_access(
                share_type,
                parsed_args.project_id)

        except Exception as e:
            raise exceptions.CommandError(
                "Failed to remove access from share type : %s" % e)
