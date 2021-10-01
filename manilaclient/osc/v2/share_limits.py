# Copyright 2021 Red Hat, Inc.
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

from osc_lib.command import command
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _


class ShareLimitsShow(command.Lister):
    """Show a list of share limits for a user."""

    _description = _("Show a list of share limits for a user.")

    def get_parser(self, prog_name):
        parser = super(ShareLimitsShow, self).get_parser(prog_name)
        limit_type_group = parser.add_mutually_exclusive_group(required=True)

        limit_type_group.add_argument(
            '--absolute',
            action='store_true',
            default=False,
            help=_('Get the absolute limits for the user')
        )
        limit_type_group.add_argument(
            '--rate',
            action='store_true',
            default=False,
            help=_('Get the API rate limits for the user')
        )

        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        # limit_type = 'absolute'
        if parsed_args.rate:
            # limit_type = 'rate'
            columns = [
                "Verb",
                "Regex",
                "URI",
                "Value",
                "Remaining",
                "Unit",
                "Next Available",
            ]
            data = list(share_client.limits.get().rate)
        else:
            columns = [
                'Name',
                'Value',
            ]

            data = list(share_client.limits.get().absolute)

        return (columns, (oscutils.get_item_properties(s, columns)
                          for s in data))
