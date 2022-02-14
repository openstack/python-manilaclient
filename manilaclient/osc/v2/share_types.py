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
from osc_lib import utils as oscutils
from oslo_utils import strutils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import constants
from manilaclient.osc import utils

LOG = logging.getLogger(__name__)

ATTRIBUTES = [
    'id',
    'name',
    'visibility',
    'is_default',
    'required_extra_specs',
    'optional_extra_specs',
    'description'
]


def format_share_type(share_type, formatter='table'):
    # share_type_access:is_public (true/false) --> visibility (public/private)
    is_public = 'share_type_access:is_public'
    visibility = 'public' if share_type._info.get(is_public) else 'private'
    share_type._info.pop(is_public, None)

    # optional_extra_specs --> extra_specs without required_extra_specs
    # required_extra_specs are displayed separately
    optional_extra_specs = share_type.extra_specs
    for key in share_type.required_extra_specs.keys():
        optional_extra_specs.pop(key, None)

    if formatter == 'table':
        share_type._info.update(
            {
                'visibility': visibility,
                'required_extra_specs': utils.format_properties(
                    share_type.required_extra_specs),
                'optional_extra_specs': utils.format_properties(
                    optional_extra_specs),
            }
        )
    else:
        share_type._info.update(
            {
                'visibility': visibility,
                'required_extra_specs': share_type.required_extra_specs,
                'optional_extra_specs': optional_extra_specs,
            }
        )

    return share_type


class CreateShareType(command.ShowOne):
    """Create new share type."""
    _description = _(
        "Create new share type")

    def get_parser(self, prog_name):
        parser = super(CreateShareType, self).get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar="<name>",
            default=None,
            help=_('Share type name')
        )
        parser.add_argument(
            'spec_driver_handles_share_servers',
            metavar="<spec_driver_handles_share_servers>",
            default=None,
            help=_("Required extra specification. "
                   "Valid values are 'true' and 'false'")
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("Share type description. "
                   "Available only for microversion >= 2.41."),
        )
        parser.add_argument(
            "--snapshot-support",
            metavar="<snapshot_support>",
            default=None,
            help=_("Boolean extra spec used for filtering of back ends "
                   "by their capability to create share snapshots."),
        )
        parser.add_argument(
            "--create-share-from-snapshot-support",
            metavar="<create_share_from_snapshot_support>",
            default=None,
            help=_("Boolean extra spec used for filtering of back ends "
                   "by their capability to create shares from snapshots."),
        )
        parser.add_argument(
            "--revert-to-snapshot-support",
            metavar="<revert_to_snapshot_support>",
            default=False,
            help=_("Boolean extra spec used for filtering of back ends "
                   "by their capability to revert shares to snapshots. "
                   "(Default is False)."),
        )
        parser.add_argument(
            "--mount-snapshot-support",
            metavar="<mount_snapshot_support>",
            default=False,
            help=_("Boolean extra spec used for filtering of back ends "
                   "by their capability to mount share snapshots. "
                   "(Default is False)."),
        )
        parser.add_argument(
            "--extra-specs",
            type=str,
            nargs='*',
            metavar='<key=value>',
            default=None,
            help=_("Extra specs key and value of share type that will be"
                   " used for share type creation. OPTIONAL: Default=None."
                   " example --extra-specs  thin_provisioning='<is> True', "
                   "replication_type=readable."),
        )
        parser.add_argument(
            '--public',
            metavar="<public>",
            default=True,
            help=_('Make type accessible to the public (default true).')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        kwargs = {
            'name': parsed_args.name
        }
        try:
            kwargs['spec_driver_handles_share_servers'] = (
                strutils.bool_from_string(
                    parsed_args.spec_driver_handles_share_servers,
                    strict=True))
        except ValueError as e:
            msg = ("Argument spec_driver_handles_share_servers "
                   "argument is not valid: %s" % str(e))
            raise exceptions.CommandError(msg)

        if parsed_args.description:
            if share_client.api_version.matches(
                    api_versions.APIVersion("2.41"),
                    api_versions.APIVersion()):
                kwargs['description'] = parsed_args.description
            else:
                raise exceptions.CommandError(
                    "Adding description to share type "
                    "is only available with API microversion >= 2.41")

        if parsed_args.public:
            kwargs['is_public'] = strutils.bool_from_string(
                parsed_args.public, default=True)

        extra_specs = {}
        if parsed_args.extra_specs:
            for item in parsed_args.extra_specs:
                (key, value) = item.split('=', 1)
                if key == 'driver_handles_share_servers':
                    msg = ("'driver_handles_share_servers' "
                           "is already set via positional argument.")
                    raise exceptions.CommandError(msg)
                else:
                    extra_specs = utils.extract_extra_specs(
                        extra_specs, [item])

        for key in constants.BOOL_SPECS:
            value = getattr(parsed_args, key)
            if value:
                extra_specs = utils.extract_extra_specs(
                    extra_specs, [key + '=' + value])

        kwargs['extra_specs'] = extra_specs

        share_type = share_client.share_types.create(**kwargs)
        formatted_type = format_share_type(share_type, parsed_args.formatter)

        return (ATTRIBUTES, oscutils.get_dict_properties(
                formatted_type._info, ATTRIBUTES))


class DeleteShareType(command.Command):
    """Delete a share type."""
    _description = _("Delete a share type")

    def get_parser(self, prog_name):
        parser = super(DeleteShareType, self).get_parser(prog_name)
        parser.add_argument(
            'share_types',
            metavar="<share_types>",
            nargs="+",
            help=_("Name or ID of the share type(s) to delete")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for share_type in parsed_args.share_types:
            try:
                share_type_obj = apiutils.find_resource(
                    share_client.share_types,
                    share_type)

                share_client.share_types.delete(share_type_obj)
            except Exception as e:
                result += 1
                LOG.error(_(
                    "Failed to delete share type with "
                    "name or ID '%(share_type)s': %(e)s"),
                    {'share_type': share_type, 'e': e})

        if result > 0:
            total = len(parsed_args.share_types)
            msg = (_("%(result)s of %(total)s share types failed "
                   "to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class SetShareType(command.Command):
    """Set share type properties."""
    _description = _("Set share type properties")

    def get_parser(self, prog_name):
        parser = super(SetShareType, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Name or ID of the share type to modify")
        )
        parser.add_argument(
            "--extra-specs",
            type=str,
            nargs='*',
            metavar='<key=value>',
            default=None,
            help=_("Extra specs key and value of share type that will be"
                   " used for share type creation. OPTIONAL: Default=None."
                   " example --extra-specs  thin_provisioning='<is> True', "
                   "replication_type=readable."),
        )
        parser.add_argument(
            '--public',
            metavar="<public>",
            default=None,
            help=_('New visibility of the share type. If set to True, '
                   'share type will be available to all projects '
                   'in the cloud. '
                   'Available only for microversion >= 2.50')
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("New description of share type. "
                   "Available only for microversion >= 2.50"),
        )
        parser.add_argument(
            '--name',
            metavar="<name>",
            default=None,
            help=_('New name of share type. '
                   'Available only for microversion >= 2.50')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types, parsed_args.share_type)

        can_update = (
            share_client.api_version >= api_versions.APIVersion('2.50'))

        kwargs = {}
        if parsed_args.name is not None:
            if can_update:
                kwargs['name'] = parsed_args.name
            else:
                raise exceptions.CommandError(
                    "Setting (new) name to share type "
                    "is only available with API microversion >= 2.50")
        if parsed_args.description is not None:
            if can_update:
                kwargs['description'] = parsed_args.description
            else:
                raise exceptions.CommandError(
                    "Setting (new) description to share type "
                    "is only available with API microversion >= 2.50")
        if parsed_args.public is not None:
            if can_update:
                kwargs['is_public'] = strutils.bool_from_string(
                    parsed_args.public, default=True)
            else:
                raise exceptions.CommandError(
                    "Setting visibility to share type "
                    "is only available with API microversion >= 2.50")
        if kwargs:
            share_type.update(**kwargs)

        if parsed_args.extra_specs:
            extra_specs = utils.extract_extra_specs(
                extra_specs={},
                specs_to_add=parsed_args.extra_specs)
            try:
                share_type.set_keys(extra_specs)
            except Exception as e:
                raise exceptions.CommandError(
                    "Failed to set share type key: %s" % e)


class UnsetShareType(command.Command):
    """Unset share type extra specs."""
    _description = _("Unset share type extra specs")

    def get_parser(self, prog_name):
        parser = super(UnsetShareType, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Name or ID of the share type to modify")
        )
        parser.add_argument(
            'extra_specs',
            metavar='<key>',
            nargs='+',
            help=_('Remove extra_specs from this share type'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types, parsed_args.share_type)

        if parsed_args.extra_specs:
            try:
                share_type.unset_keys(parsed_args.extra_specs)
            except Exception as e:
                raise exceptions.CommandError(
                    "Failed to remove share type extra spec: %s" % e)


class ListShareType(command.Lister):
    """List Share Types."""
    _description = _("List share types")

    def get_parser(self, prog_name):
        parser = super(ListShareType, self).get_parser(prog_name)
        parser.add_argument(
            '--all',
            action='store_true',
            default=False,
            help=_('Display all share types whatever public or private. '
                   'Default=False. (Admin only)'),
        )
        parser.add_argument(
            '--extra-specs',
            type=str,
            nargs='*',
            metavar='<key=value>',
            default=None,
            help=_('Filter share types with extra specs (key=value). '
                   'Available only for API microversion >= 2.43. '
                   'OPTIONAL: Default=None.'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        search_opts = {}
        if parsed_args.extra_specs:
            if share_client.api_version < api_versions.APIVersion("2.43"):
                raise exceptions.CommandError(
                    "Filtering by 'extra_specs' is available only with "
                    "API microversion '2.43' and above.")

            search_opts = {
                'extra_specs': utils.extract_extra_specs(
                    extra_specs={},
                    specs_to_add=parsed_args.extra_specs)
            }

        share_types = share_client.share_types.list(
            search_opts=search_opts,
            show_all=parsed_args.all)

        formatted_types = []
        for share_type in share_types:
            formatted_types.append(format_share_type(share_type,
                                                     parsed_args.formatter))

        values = (oscutils.get_dict_properties(
            s._info, ATTRIBUTES) for s in formatted_types)

        columns = utils.format_column_headers(ATTRIBUTES)

        return (columns, values)


class ShowShareType(command.ShowOne):
    """Show a share type."""
    _description = _("Display share type details")

    def get_parser(self, prog_name):
        parser = super(ShowShareType, self).get_parser(prog_name)
        parser.add_argument(
            'share_type',
            metavar="<share_type>",
            help=_("Share type to display (name or ID)")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_type = apiutils.find_resource(
            share_client.share_types,
            parsed_args.share_type)

        formatted_type = format_share_type(share_type, parsed_args.formatter)

        return (ATTRIBUTES, oscutils.get_dict_properties(
            formatted_type._info, ATTRIBUTES))
