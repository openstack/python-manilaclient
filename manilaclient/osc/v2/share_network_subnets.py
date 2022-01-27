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

import logging
from operator import xor

from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient.common._i18n import _


LOG = logging.getLogger(__name__)


class CreateShareNetworkSubnet(command.ShowOne):
    """Create a share network subnet."""
    _description = _("Create a share network subnet")

    def get_parser(self, prog_name):
        parser = super(CreateShareNetworkSubnet, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Share network name or ID.")
        )
        parser.add_argument(
            "--neutron-net-id",
            metavar="<neutron-net-id>",
            default=None,
            help=_("Neutron network ID. Used to set up network for share "
                   "servers (optional). Should be defined together with "
                   "'--neutron-subnet-id'.")
        )
        parser.add_argument(
            "--neutron-subnet-id",
            metavar="<neutron-subnet-id>",
            default=None,
            help=_("Neutron subnet ID. Used to set up network for share "
                   "servers (optional). Should be defined together with "
                   "'--neutron-net-id' to which this subnet belongs to. ")
        )
        parser.add_argument(
            "--availability-zone",
            metavar="<availability-zone>",
            default=None,
            help=_("Optional availability zone that the subnet is available "
                   "within (Default=None). If None, the subnet will be "
                   "considered as being available across all availability "
                   "zones.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        if xor(bool(parsed_args.neutron_net_id),
               bool(parsed_args.neutron_subnet_id)):
            raise exceptions.CommandError(
                "Both neutron_net_id and neutron_subnet_id should be "
                "specified. Alternatively, neither of them should be "
                "specified.")

        share_network_id = oscutils.find_resource(
            share_client.share_networks,
            parsed_args.share_network).id

        share_network_subnet = share_client.share_network_subnets.create(
            neutron_net_id=parsed_args.neutron_net_id,
            neutron_subnet_id=parsed_args.neutron_subnet_id,
            availability_zone=parsed_args.availability_zone,
            share_network_id=share_network_id
        )
        subnet_data = share_network_subnet._info

        return self.dict2columns(subnet_data)


class DeleteShareNetworkSubnet(command.Command):
    """Delete a share network subnet."""
    _description = _("Delete a share network subnet")

    def get_parser(self, prog_name):
        parser = super(DeleteShareNetworkSubnet, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Share network name or ID.")
        )
        parser.add_argument(
            "share_network_subnet",
            metavar="<share-network-subnet>",
            nargs="+",
            help=_("ID(s) of share network subnet(s) to be deleted.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        share_network_id = oscutils.find_resource(
            share_client.share_networks,
            parsed_args.share_network).id

        for subnet in parsed_args.share_network_subnet:
            try:
                share_client.share_network_subnets.delete(
                    share_network_id,
                    subnet)

            except Exception as e:
                result += 1
                LOG.error(f"Failed to delete share network subnet with "
                          f"ID {subnet}: {e}")
        if result > 0:
            total = len(parsed_args.share_network_subnet)
            raise exceptions.CommandError(
                f"{result} of {total} share network subnets failed to be "
                f"deleted.")


class ShowShareNetworkSubnet(command.ShowOne):
    """Show share network subnet."""
    _description = _("Show share network subnet")

    def get_parser(self, prog_name):
        parser = super(ShowShareNetworkSubnet, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Share network name or ID.")
        )
        parser.add_argument(
            "share_network_subnet",
            metavar="<share-network-subnet>",
            help=_("ID of share network subnet to show.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_network_id = oscutils.find_resource(
            share_client.share_networks,
            parsed_args.share_network).id

        share_network_subnet = share_client.share_network_subnets.get(
            share_network_id,
            parsed_args.share_network_subnet)

        return self.dict2columns(share_network_subnet._info)
