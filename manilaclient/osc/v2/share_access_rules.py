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
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.osc import utils

ACCESS_RULE_ATTRIBUTES = [
    'id',
    'share_id',
    'access_level',
    'access_to',
    'access_type',
    'state',
    'access_key',
    'created_at',
    'updated_at',
    'properties'
]

LOG = logging.getLogger(__name__)


class ShareAccessAllow(command.ShowOne):
    """Create a new share access rule."""
    _description = _("Create new share access rule")

    def get_parser(self, prog_name):
        parser = super(ShareAccessAllow, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of the NAS share to modify.')
        )
        parser.add_argument(
            'access_type',
            metavar="<access_type>",
            help=_('Access rule type (only "ip", "user" (user or group), '
                   '"cert" or "cephx" are supported).')
        )
        parser.add_argument(
            'access_to',
            metavar="<access_to>",
            help=_('Value that defines access.')
        )
        # metadata --> properties in osc
        parser.add_argument(
            '--properties',
            type=str,
            nargs='*',
            metavar='<key=value>',
            help=_('Space separated list of key=value pairs of properties. '
                   'OPTIONAL: Default=None. '
                   'Available only for API microversion >= 2.45.'),
        )
        parser.add_argument(
            '--access-level',
            metavar="<access_level>",
            type=str,
            default=None,
            choices=['rw', 'ro'],
            help=_('Share access level ("rw" and "ro" access levels '
                   'are supported). Defaults to rw.')
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            help=_("Wait for share access rule creation.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        properties = {}
        if parsed_args.properties:
            if share_client.api_version >= api_versions.APIVersion("2.45"):
                properties = utils.extract_properties(parsed_args.properties)
            else:
                raise exceptions.CommandError(
                    "Adding properties to access rules is supported only "
                    "with API microversion 2.45 and beyond")
        try:
            share_access_rule = share.allow(
                access_type=parsed_args.access_type,
                access=parsed_args.access_to,
                access_level=parsed_args.access_level,
                metadata=properties
            )
            if parsed_args.wait:
                if not oscutils.wait_for_status(
                    status_f=share_client.share_access_rules.get,
                    res_id=share_access_rule['id'],
                    status_field='state'
                ):
                    LOG.error(_("ERROR: Share access rule is in error state."))

                share_access_rule = oscutils.find_resource(
                    share_client.share_access_rules,
                    share_access_rule['id'])._info
            share_access_rule.update(
                {
                    'properties': utils.format_properties(
                        share_access_rule.pop('metadata', {}))
                }
            )
            return (ACCESS_RULE_ATTRIBUTES, oscutils.get_dict_properties(
                    share_access_rule,
                    ACCESS_RULE_ATTRIBUTES))
        except Exception as e:
            raise exceptions.CommandError(
                "Failed to create access to share "
                "'%s': %s" % (share, e))


class ShareAccessDeny(command.Command):
    """Delete a share access rule."""
    _description = _("Delete a share access rule")

    def get_parser(self, prog_name):
        parser = super(ShareAccessDeny, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of the NAS share to modify.')
        )
        parser.add_argument(
            'id',
            metavar="<id>",
            help=_('ID of the access rule to be deleted.')
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for share access rule deletion")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)
        error = None
        try:
            share.deny(parsed_args.id)
            if parsed_args.wait:
                if not oscutils.wait_for_delete(
                        manager=share_client.share_access_rules,
                        res_id=parsed_args.id):
                    error = _("Failed to delete share access rule with ID: %s"
                              % parsed_args.id)
        except Exception as e:
            error = e
        if error:
            raise exceptions.CommandError(_(
                "Failed to delete share access rule for share "
                "'%s': %s" % (share, error)))


class ListShareAccess(command.Lister):
    """List share access rules."""
    _description = _("List share access rule")

    def get_parser(self, prog_name):
        parser = super(ListShareAccess, self).get_parser(prog_name)
        parser.add_argument(
            'share',
            metavar="<share>",
            help=_('Name or ID of the share.')
        )

        # metadata --> properties in osc
        parser.add_argument(
            '--properties',
            type=str,
            nargs='*',
            metavar='<key=value>',
            default=None,
            help=_('Filters results by properties (key=value). '
                   'OPTIONAL: Default=None. '
                   'Available only for API microversion >= 2.45'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share = apiutils.find_resource(share_client.shares,
                                       parsed_args.share)

        if share_client.api_version >= api_versions.APIVersion("2.45"):
            search_opts = {}
            if parsed_args.properties:
                search_opts = {
                    'metadata': utils.extract_properties(
                        parsed_args.properties)
                }
            access_list = share_client.share_access_rules.access_list(
                share,
                search_opts)
        elif parsed_args.properties:
            raise exceptions.CommandError(
                "Filtering access rules by properties is supported only "
                "with API microversion 2.45 and beyond.")
        else:
            access_list = share.access_list()

        list_of_keys = [
            'ID',
            'Access Type',
            'Access To',
            'Access Level',
            'State'
        ]

        if share_client.api_version >= api_versions.APIVersion("2.21"):
            list_of_keys.append('Access Key')

        if share_client.api_version >= api_versions.APIVersion("2.33"):
            list_of_keys.append('Created At')
            list_of_keys.append('Updated At')

        values = (oscutils.get_item_properties(
            a, list_of_keys) for a in access_list)

        return (list_of_keys, values)


class ShowShareAccess(command.ShowOne):
    """Display a share access rule."""
    _description = _(
        "Display a share access rule. "
        "Available for API microversion 2.45 and higher")

    def get_parser(self, prog_name):
        parser = super(ShowShareAccess, self).get_parser(prog_name)
        parser.add_argument(
            'access_id',
            metavar="<access_id>",
            help=_('ID of the NAS share access rule.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        if share_client.api_version >= api_versions.APIVersion("2.45"):
            access_rule = share_client.share_access_rules.get(
                parsed_args.access_id
            )
            access_rule._info.update(
                {
                    'properties': utils.format_properties(
                        access_rule._info.pop('metadata', {}))
                }
            )
            return (ACCESS_RULE_ATTRIBUTES, oscutils.get_dict_properties(
                access_rule._info,
                ACCESS_RULE_ATTRIBUTES))
        else:
            raise exceptions.CommandError(
                "Displaying share access rule details is only available "
                "with API microversion 2.45 and higher.")


class SetShareAccess(command.Command):
    """Set properties to share access rule."""
    _description = _(
        "Set properties to share access rule. "
        "Available for API microversion 2.45 and higher")

    def get_parser(self, prog_name):
        parser = super(SetShareAccess, self).get_parser(prog_name)
        parser.add_argument(
            'access_id',
            metavar="<access_id>",
            help=_('ID of the NAS share access rule.')
        )
        # metadata --> properties in osc
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            default={},
            action=parseractions.KeyValueAction,
            help=_('Set a property to this share access rule. '
                   '(Repeat option to set multiple properties) '
                   'Available only for API microversion >= 2.45.'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        if share_client.api_version >= api_versions.APIVersion("2.45"):
            access_rule = share_client.share_access_rules.get(
                parsed_args.access_id
            )
            try:
                share_client.share_access_rules.set_metadata(
                    access_rule,
                    parsed_args.property)
            except Exception as e:
                raise exceptions.CommandError(
                    "Failed to set properties to share access rule with ID "
                    "'%s': %s" % (access_rule.id, e))

        else:
            raise exceptions.CommandError(
                "Setting properties to access rule is supported only "
                "with API microversion 2.45 and higher")


class UnsetShareAccess(command.Command):
    """Unset properties of share access rule."""
    _description = _(
        "Unset properties of share access rule. "
        "Available for API microversion 2.45 and higher")

    def get_parser(self, prog_name):
        parser = super(UnsetShareAccess, self).get_parser(prog_name)
        parser.add_argument(
            'access_id',
            metavar="<access_id>",
            help=_('ID of the NAS share access rule.')
        )
        # metadata --> properties in osc
        parser.add_argument(
            '--property',
            metavar='<key>',
            action='append',
            help=_('Remove property from share access rule. '
                   '(Repeat option to remove multiple properties) '
                   'Available only for API microversion >= 2.45.'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        if share_client.api_version >= api_versions.APIVersion("2.45"):
            access_rule = share_client.share_access_rules.get(
                parsed_args.access_id
            )
            if parsed_args.property:
                try:
                    share_client.share_access_rules.unset_metadata(
                        access_rule,
                        parsed_args.property)
                except Exception as e:
                    raise exceptions.CommandError(
                        "Failed to unset properties for share access rule "
                        "with ID '%s': %s" % (access_rule.id, e))
            else:
                raise exceptions.CommandError(
                    "Please specify '--property <key>' to unset a property. ")

        else:
            raise exceptions.CommandError(
                "Option to unset properties of access rule is available only "
                "for API microversion 2.45 and higher")
