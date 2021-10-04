# Copyright 2021 NetApp, Inc.
# All Rights Reserved.
#
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
from osc_lib import utils as osc_utils

from manilaclient.common._i18n import _


class ShareInstanceListExportLocation(command.Lister):
    """List share instance export locations."""
    _description = _("List share instance export locations")

    def get_parser(self, prog_name):
        parser = super(
            ShareInstanceListExportLocation, self).get_parser(prog_name)
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
            instance,
            search_opts=None)

        columns = [
            'ID',
            'Path',
            'Is Admin Only',
            'Preferred',
        ]

        data = (
            osc_utils.get_dict_properties(export_location._info, columns)
            for export_location in export_locations
        )

        return (columns, data)


class ShareInstanceShowExportLocation(command.ShowOne):
    """Display the export location for a share instance."""
    _description = _(
        "Show export location for a share instance.")

    def get_parser(self, prog_name):
        parser = super(
            ShareInstanceShowExportLocation, self).get_parser(prog_name)
        parser.add_argument(
            "instance",
            metavar="<instance>",
            help=_("Name or ID of the share instance")
        )
        parser.add_argument(
            "export_location",
            metavar="<export_location>",
            help=_("ID of the share instance export location.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_instance = osc_utils.find_resource(
            share_client.share_instances,
            parsed_args.instance)

        share_instance_export_locations = (
            share_client.share_instance_export_locations.get(
                share_instance.id,
                parsed_args.export_location)
        )

        data = share_instance_export_locations._info
        data.pop('links', None)

        return self.dict2columns(data)
