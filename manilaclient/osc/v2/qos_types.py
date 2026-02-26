# Copyright (c) 2025 Cloudification GmbH.
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
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _
from manilaclient.common.apiclient import utils as apiutils
from manilaclient.common import constants
from manilaclient.osc import utils

LOG = logging.getLogger(__name__)

ATTRIBUTES = [
    'id',
    'name',
    'description',
    'specs',
    'created_at',
    'updated_at',
]


def format_qos_type(qos_type, formatter='table'):
    specs = qos_type.specs
    if formatter == 'table':
        qos_type._info.update({'specs': utils.format_properties(specs)})
    else:
        qos_type._info.update({'specs': specs})
    return qos_type


class CreateQosType(command.ShowOne):
    """Create new qos type."""

    _description = _("Create new qos type")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar="<name>",
            help=_('QoS type name. This must be unique.'),
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("QoS type description."),
        )
        parser.add_argument(
            "--spec",
            type=str,
            metavar='<key=value>',
            action='append',
            default=None,
            help=_(
                "Spec key and value of QoS type that will be"
                " used for QoS type creation. OPTIONAL: Default=None."
                " Example: --spec qos_type='fixed' --spec peak_iops=300."
            ),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        kwargs = {'name': parsed_args.name}
        if parsed_args.description:
            kwargs['description'] = parsed_args.description

        if parsed_args.spec:
            specs = utils.extract_properties(parsed_args.spec)
            kwargs['specs'] = specs

        qos_type = share_client.qos_types.create(**kwargs)
        formatted_type = format_qos_type(qos_type, parsed_args.formatter)

        return (
            ATTRIBUTES,
            oscutils.get_dict_properties(formatted_type._info, ATTRIBUTES),
        )


class DeleteQosType(command.Command):
    """Delete a qos type."""

    _description = _("Delete a qos type")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'qos_types',
            metavar="<qos_types>",
            nargs="+",
            help=_("Name or ID of the qos type(s) to delete"),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for qos_type in parsed_args.qos_types:
            try:
                qos_type_obj = apiutils.find_resource(
                    share_client.qos_types, qos_type
                )

                share_client.qos_types.delete(qos_type_obj)
            except Exception as e:
                result += 1
                LOG.error(
                    _(
                        "Failed to delete qos type with "
                        "name or ID '%(qos_type)s': %(e)s"
                    ),
                    {'qos_type': qos_type, 'e': e},
                )

        if result > 0:
            total = len(parsed_args.qos_types)
            msg = _("%(result)s of %(total)s qos types failed to delete.") % {
                'result': result,
                'total': total,
            }
            raise exceptions.CommandError(msg)


class SetQosType(command.Command):
    """Set qos type description or specs."""

    _description = _("Set qos type description or specs")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'qos_type',
            metavar="<qos_type>",
            help=_("Name or ID of the qos type to modify"),
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("New description of qos type."),
        )
        parser.add_argument(
            "--spec",
            type=str,
            metavar='<key=value>',
            action='append',
            default=None,
            help=_(
                "Spec key and value of qos type that will be "
                "used for QoS type. OPTIONAL: Default=None. For "
                "example --spec qos_type='fixed' --spec peak_iops=300"
            ),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        qos_type = apiutils.find_resource(
            share_client.qos_types, parsed_args.qos_type
        )

        kwargs = {}
        if parsed_args.description:
            kwargs['description'] = parsed_args.description
        if kwargs:
            try:
                qos_type.update(**kwargs)
            except Exception as e:
                raise exceptions.CommandError(
                    _("Failed to set qos type description: %s") % e
                )

        # These are dict of key=value to be added as qos type specs.
        if parsed_args.spec:
            specs = utils.extract_properties(parsed_args.spec)
            try:
                qos_type.set_keys(specs)
            except Exception as e:
                raise exceptions.CommandError(
                    _("Failed to set qos type spec: %s") % e
                )


class UnsetQosType(command.Command):
    """Unset qos type specs."""

    _description = _("Unset qos type specs")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'qos_type',
            metavar="<qos_type>",
            help=_("Name or ID of the qos type to modify"),
        )
        parser.add_argument(
            "--description",
            action='store_true',
            help=_("Unset qos type description."),
        )
        parser.add_argument(
            '--spec',
            metavar='<key>',
            action='append',
            help=_('Remove specified spec from this qos type'),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        qos_type = apiutils.find_resource(
            share_client.qos_types, parsed_args.qos_type
        )

        kwargs = {}
        if parsed_args.description:
            kwargs['description'] = None
        if kwargs:
            try:
                qos_type.update(**kwargs)
            except Exception as e:
                raise exceptions.CommandError(
                    _("Failed to unset qos type description: %s") % e
                )

        # These are list of keys to be deleted from qos type specs.
        if parsed_args.spec:
            try:
                qos_type.unset_keys(parsed_args.spec)
            except Exception as e:
                raise exceptions.CommandError(
                    _("Failed to remove qos type spec: %s") % e
                )


class ListQosType(command.Lister):
    """List Qos Types."""

    _description = _("List qos types")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar="<name>",
            default=None,
            help=_('Filter results by name. Default=None.'),
        )
        parser.add_argument(
            '--description',
            metavar="<description>",
            default=None,
            help=_("Filter results by description. Default=None."),
        )
        parser.add_argument(
            "--name~",
            metavar="<name~>",
            default=None,
            help=_("Filter results matching a qos name pattern. "),
        )
        parser.add_argument(
            '--description~',
            metavar="<description~>",
            default=None,
            help=_("Filter results matching a qos description pattern."),
        )
        parser.add_argument(
            "--limit",
            metavar="<num-qos-types>",
            type=int,
            default=None,
            action=parseractions.NonNegativeAction,
            help=_("Limit the number of qos types returned. Default=None."),
        )
        parser.add_argument(
            '--offset',
            metavar="<offset>",
            default=None,
            help=_('Start position of qos type records listing.'),
        )
        parser.add_argument(
            '--sort-key',
            '--sort_key',
            metavar='<sort_key>',
            type=str,
            default=None,
            help=_(
                'Key to be sorted with, available keys are '
                '%(keys)s. Default=None.'
            )
            % {'keys': constants.QOS_TYPE_SORT_KEY_VALUES},
        )
        parser.add_argument(
            '--sort-dir',
            '--sort_dir',
            metavar='<sort_dir>',
            type=str,
            default=None,
            help=_(
                'Sort direction, available values are '
                '%(dirs)s. OPTIONAL: Default=None.'
            )
            % {'dirs': constants.SORT_DIR_VALUES},
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        search_opts = {
            'name': parsed_args.name,
            'description': parsed_args.description,
            'limit': parsed_args.limit,
            'offset': parsed_args.offset,
        }
        search_opts['name~'] = getattr(parsed_args, 'name~')
        search_opts['description~'] = getattr(parsed_args, 'description~')

        qos_types = share_client.qos_types.list(
            search_opts=search_opts,
            sort_key=parsed_args.sort_key,
            sort_dir=parsed_args.sort_dir,
        )

        formatted_types = []
        for qos_type in qos_types:
            formatted_types.append(
                format_qos_type(qos_type, parsed_args.formatter)
            )

        values = (
            oscutils.get_dict_properties(s._info, ATTRIBUTES)
            for s in formatted_types
        )

        columns = utils.format_column_headers(ATTRIBUTES)

        return (columns, values)


class ShowQosType(command.ShowOne):
    """Show a qos type."""

    _description = _("Display qos type details")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'qos_type',
            metavar="<qos_type>",
            help=_("Qos type to display (name or ID)"),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        qos_type = apiutils.find_resource(
            share_client.qos_types, parsed_args.qos_type
        )

        formatted_type = format_qos_type(qos_type, parsed_args.formatter)

        return (
            ATTRIBUTES,
            oscutils.get_dict_properties(formatted_type._info, ATTRIBUTES),
        )
