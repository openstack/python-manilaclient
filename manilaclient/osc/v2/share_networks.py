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

import logging

from openstackclient.identity import common as identity_common
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils as oscutils

from manilaclient import api_versions
from manilaclient.common._i18n import _
from manilaclient.common import cliutils

LOG = logging.getLogger(__name__)


class ListShareNetwork(command.Lister):
    _description = _("List share networks")

    def get_parser(self, prog_name):
        parser = super(ListShareNetwork, self).get_parser(prog_name)

        parser.add_argument(
            '--name',
            metavar="<share-network>",
            help=_('Filter share networks by name')
        )
        parser.add_argument(
            '--name~',
            metavar="<share-network-name-pattern>",
            help=_('Filter share networks by name-pattern. Available only '
                   'for microversion >= 2.36.')
        )
        parser.add_argument(
            '--description',
            metavar="<share-network-description>",
            help=_('Filter share networks by description. Available '
                   'only for microversion >= 2.36')
        )
        parser.add_argument(
            '--description~',
            metavar="<share-network-description-pattern>",
            help=_('Filter share networks by description-pattern. Available '
                   'only for microversion >= 2.36.')
        )
        parser.add_argument(
            '--all-projects',
            action='store_true',
            default=False,
            help=_('Include all projects (admin only)'),
        )
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_('Filter share networks by project (name or ID) '
                   '(admin only)')
        )
        identity_common.add_project_domain_option_to_parser(parser)
        parser.add_argument(
            '--created-since',
            metavar='<yyyy-mm-dd>',
            help=_('Filter share networks by date they were created after. '
                   'The date can be in the format yyyy-mm-dd.')
        )
        parser.add_argument(
            '--created-before',
            metavar='<yyyy-mm-dd>',
            help=_('Filter share networks by date they were created before. '
                   'The date can be in the format yyyy-mm-dd.')
        )
        parser.add_argument(
            '--security-service',
            metavar='<security-service>',
            help=_('Filter share networks by the name or ID of a security '
                   'service attached to the network.')
        )
        parser.add_argument(
            '--neutron-net-id',
            metavar='<neutron-net-id>',
            help=_('Filter share networks by the ID of a neutron network.')
        )
        parser.add_argument(
            '--neutron-subnet-id',
            metavar='<neutron-subnet-id>',
            help=_('Filter share networks by the ID of a neutron sub network.')
        )
        parser.add_argument(
            '--network-type',
            metavar='<network-type>',
            help=_('Filter share networks by the type of network. Examples '
                   'include "flat", "vlan", "vxlan", "geneve", etc.')
        )
        parser.add_argument(
            '--segmentation-id',
            metavar='<segmentation-id>',
            help=_('Filter share networks by the segmentation ID of network. '
                   'Relevant only for segmented networks such as "vlan", '
                   '"vxlan", "geneve", etc.')
        )
        parser.add_argument(
            '--cidr',
            metavar='<X.X.X.X/X>',
            help=_('Filter share networks by the CIDR of network.')
        )
        parser.add_argument(
            '--ip-version',
            metavar='4/6',
            choices=['4', '6'],
            help=_('Filter share networks by the IP Version of the network, '
                   'either 4 or 6.')
        )
        parser.add_argument(
            '--detail',
            action='store_true',
            default=False,
            help=_("List share networks with details")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        columns = ['ID', 'Name']

        if parsed_args.detail:
            columns.extend([
                'Status',
                'Created At',
                'Updated At',
                'Description',
            ])

        project_id = None
        if parsed_args.project:
            project_id = identity_common.find_project(
                identity_client,
                parsed_args.project,
                parsed_args.project_domain).id

        # set value of 'all_tenants' when using project option
        all_tenants = bool(parsed_args.project) or parsed_args.all_projects

        if parsed_args.all_projects:
            columns.append('Project ID')

        search_opts = {
            'all_tenants': all_tenants,
            'project_id': project_id,
            'name': parsed_args.name,
            'created_since': parsed_args.created_since,
            'created_before': parsed_args.created_before,
            'neutron_net_id': parsed_args.neutron_net_id,
            'neutron_subnet_id': parsed_args.neutron_subnet_id,
            'network_type': parsed_args.network_type,
            'segmentation_id': parsed_args.segmentation_id,
            'cidr': parsed_args.cidr,
            'ip_version': parsed_args.ip_version,
            'security_service': parsed_args.security_service,
        }

        if share_client.api_version >= api_versions.APIVersion("2.36"):
            search_opts['name~'] = getattr(parsed_args, 'name~')
            search_opts['description~'] = getattr(parsed_args, 'description~')
            search_opts['description'] = parsed_args.description
        elif (parsed_args.description or getattr(parsed_args, 'name~') or
              getattr(parsed_args, 'description~')):
            raise exceptions.CommandError(
                "Pattern based filtering (name~, description~ and description)"
                " is only available with manila API version >= 2.36")

        data = share_client.share_networks.list(search_opts=search_opts)

        return (
            columns,
            (oscutils.get_item_properties(s, columns) for s in data)
        )


class ShowShareNetwork(command.ShowOne):
    """Display a share network"""
    _description = _("Show details about a share network")

    def get_parser(self, prog_name):
        parser = super(ShowShareNetwork, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Name or ID of the share network to display")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_network = oscutils.find_resource(
            share_client.share_networks,
            parsed_args.share_network)

        data = share_network._info

        # Add security services information
        security_services = share_client.security_services.list(
            search_opts={'share_network_id': share_network.id}, detailed=False)
        data['security_services'] = [
            {
                'security_service_name': ss.name,
                'security_service_id': ss.id,
            }
            for ss in security_services
        ]

        if parsed_args.formatter == 'table':
            data['share_network_subnets'] = (
                cliutils.convert_dict_list_to_string(
                    data['share_network_subnets'])
            )
            data['security_services'] = cliutils.convert_dict_list_to_string(
                data['security_services']
            )

        data.pop('links', None)

        return self.dict2columns(data)


class CreateShareNetwork(command.ShowOne):
    """Create a share network."""
    _description = _("Create a share network")

    def get_parser(self, prog_name):
        parser = super(CreateShareNetwork, self).get_parser(prog_name)
        parser.add_argument(
            "--name",
            metavar="<share-network>",
            help=_("Add a name to the share network (Optional)")
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("Add a description to the share network (Optional).")
        )
        parser.add_argument(
            "--neutron-net-id",
            metavar="<neutron-net-id>",
            default=None,
            help=_("ID of the neutron network that must be associated with "
                   "the share network (Optional). The network specified will "
                   "be associated with the 'default' share network subnet, "
                   "unless 'availability-zone' is also specified.")
        )
        parser.add_argument(
            "--neutron-subnet-id",
            metavar="<neutron-subnet-id>",
            default=None,
            help=_("ID of the neutron sub-network that must be associated "
                   "with the share network (Optional). The subnet specified "
                   "will be associated with the 'default' share network "
                   "subnet, unless 'availability-zone' is also specified.")
        )
        parser.add_argument(
            "--availability-zone",
            metavar="<availability-zone>",
            default=None,
            help=_("Name or ID of the avalilability zone to assign the "
                   "specified network subnet parameters to. Must be used "
                   "in conjunction with 'neutron-net-id' and "
                   "'neutron-subnet-id'. Do not specify this parameter if "
                   "the network must be available across all availability "
                   "zones ('default' share network subnet). Available "
                   "only for microversion >= 2.51.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        availability_zone = None
        if (parsed_args.availability_zone and
                share_client.api_version < api_versions.APIVersion("2.51")):
            raise exceptions.CommandError(
                "Availability zone can be specified only with manila API "
                "version >= 2.51")
        elif parsed_args.availability_zone:
            availability_zone = oscutils.find_resource(
                share_client.availability_zones,
                parsed_args.availability_zone).name

        share_network = share_client.share_networks.create(
            name=parsed_args.name,
            description=parsed_args.description,
            neutron_net_id=parsed_args.neutron_net_id,
            neutron_subnet_id=parsed_args.neutron_subnet_id,
            availability_zone=availability_zone,
        )
        share_network_data = share_network._info
        share_network_data.pop('links', None)
        if parsed_args.formatter == 'table':
            share_network_data['share_network_subnets'] = (
                cliutils.convert_dict_list_to_string(
                    share_network_data['share_network_subnets'])
            )
        return self.dict2columns(share_network_data)


class DeleteShareNetwork(command.Command):
    """Delete one or more share networks"""
    _description = _("Delete one or more share networks")

    def get_parser(self, prog_name):
        parser = super(DeleteShareNetwork, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            nargs="+",
            help=_("Name or ID of the share network(s) to delete")
        )
        parser.add_argument(
            "--wait",
            action='store_true',
            default=False,
            help=_("Wait for the share network(s) to be deleted")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for share_network in parsed_args.share_network:
            try:
                share_network_obj = oscutils.find_resource(
                    share_client.share_networks,
                    share_network)
                share_client.share_networks.delete(
                    share_network_obj)

                if parsed_args.wait:
                    if not oscutils.wait_for_delete(
                            manager=share_client.share_networks,
                            res_id=share_network_obj.id):
                        result += 1
            except Exception as e:
                result += 1
                LOG.error(f"Failed to delete share network with "
                          f"name or ID {share_network}: {e}")

        if result > 0:
            total = len(parsed_args.share_network)
            msg = f"{result} of {total} share networks failed to be deleted."
            raise exceptions.CommandError(msg)


class SetShareNetwork(command.Command):
    """Set share network properties."""
    _description = _("Set share network properties")

    def get_parser(self, prog_name):
        parser = super(SetShareNetwork, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_('Name or ID of the share network to set a property for')
        )
        parser.add_argument(
            "--name",
            metavar="<name>",
            default=None,
            help=_("Set a new name to the share network.")
        )
        parser.add_argument(
            "--description",
            metavar="<description>",
            default=None,
            help=_("Set a new description to the share network.")
        )
        parser.add_argument(
            "--status",
            metavar="<status>",
            choices=['active', 'error', 'network_change'],
            help=_("Assign a status to the share network (Admin only). "
                   "Options include : active, error, network_change. "
                   "Available only for microversion >= 2.63.")
        )
        parser.add_argument(
            '--neutron-net-id',
            metavar='<neutron-net-id>',
            help=_("Update the neutron network associated with the default "
                   "share network subnet. If a default share network subnet "
                   "is not present or if the share network is in use, setting "
                   "this will fail.")
        )
        parser.add_argument(
            '--neutron-subnet-id',
            metavar='<neutron-subnet-id>',
            help=_("Update the neutron subnetwork associated with the default "
                   "share network subnet. If a default share network subnet "
                   "is not present or if the share network is in use, setting "
                   "this will fail.")
        )
        parser.add_argument(
            '--current-security-service',
            metavar='<security-service>',
            help=_("Name or ID of a security service that is currently "
                   "associated with a share network that must be replaced. "
                   "Replacing a security service is only available for "
                   "microversions >= 2.63.")
        )
        parser.add_argument(
            '--new-security-service',
            metavar='<security-service>',
            help=_("Name or ID of a security service that must be associated "
                   "with the share network. When replacing a security "
                   "service, the current security service must also be "
                   "provided with the '--current-security-service' option. "
                   "Replacing a security service is only available for "
                   "microversions >= 2.63.")
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help=_("Run a dry-run of a security service replacement. "
                   "Available only for microversion >=2.63")
        )
        parser.add_argument(
            '--restart-check',
            action='store_true',
            help=_("Restart a dry-run of a security service "
                   "replacement. Helpful when check results are "
                   "stale. Available only for microversion >=2.63.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        share_network = oscutils.find_resource(share_client.share_networks,
                                               parsed_args.share_network)

        kwargs = {}

        # some args are only for newer API micro-version
        if share_client.api_version < api_versions.APIVersion("2.63"):
            new_args = ('status', 'check_only', 'restart_check',
                        'current_security_service')
            invalid_args = [
                arg for arg in new_args
                if getattr(parsed_args, arg) is not None
            ]
            raise exceptions.CommandError(
                f"Use of {' '.join(invalid_args)} is only available for API "
                f"microversions >= 2.63.")

        # If "--check-only" and "--restart-check" are used, a new security
        # service option must be supplied
        if parsed_args.check_only or parsed_args.restart_check:
            if not parsed_args.new_security_service:
                raise exceptions.CommandError(
                    _("Must provide new security service with --check-only "
                      "and --restart-check."))

        if parsed_args.name is not None:
            kwargs['name'] = parsed_args.name
        if parsed_args.description is not None:
            kwargs['description'] = parsed_args.description
        if parsed_args.neutron_net_id is not None:
            kwargs['neutron_net_id'] = parsed_args.neutron_net_id
        if parsed_args.neutron_subnet_id is not None:
            kwargs['neutron_subnet_id'] = parsed_args.neutron_subnet_id

        if kwargs:
            try:
                share_client.share_networks.update(
                    share_network,
                    **kwargs
                )
            except Exception as e:
                result += 1
                LOG.error(f"Failed to set share network properties "
                          f"{kwargs}: {e}")

        if parsed_args.status:
            try:
                share_client.share_networks.reset_state(
                    share_network,
                    parsed_args.status
                )
            except Exception as e:
                result += 1
                LOG.error(f"Failed to update share network status to "
                          f"{parsed_args.status}: {e}")

        new_security_service = current_security_service = None
        if parsed_args.new_security_service:
            new_security_service = oscutils.find_resource(
                share_client.security_services,
                parsed_args.new_security_service)
        if parsed_args.current_security_service:
            current_security_service = oscutils.find_resource(
                share_client.security_services,
                parsed_args.current_security_service)

        if new_security_service and not current_security_service:
            try:
                if parsed_args.check_only:
                    check_result = share_client.share_networks\
                        .add_security_service_check(
                            share_network, new_security_service,
                            reset_operation=parsed_args.restart_check)
                    is_compatible = check_result[1].get('compatible')
                    # NOTE(gouthamr): We're logging to the console here,
                    # because there's no need to print useful
                    # information beyond the result. Use of error
                    # logging is a hack, since other kinds of logs may
                    # not print to console by default.
                    if is_compatible is None:
                        LOG.error("Security service check has been "
                                  "successfully initiated, please retry "
                                  "after some time.")
                    elif is_compatible:
                        LOG.error(
                            f"Security service "
                            f"{parsed_args.new_security_service} can "
                            f"be added to share network "
                            f"{parsed_args.share_network}.")
                    else:
                        LOG.error(
                            f"Security service "
                            f"{parsed_args.new_security_service} cannot "
                            f"be added to share network "
                            f"{parsed_args.share_network}.")
                else:
                    share_client.share_networks.add_security_service(
                        share_network, new_security_service)
            except Exception as e:
                result += 1
                LOG.error(f"Failed to add security service  "
                          f"{parsed_args.new_security_service} to "
                          f"share network {parsed_args.share_network}: {e}")

        if new_security_service and current_security_service:
            try:
                if parsed_args.check_only:
                    check_result = share_client.share_networks.\
                        update_share_network_security_service_check(
                            share_network,
                            current_security_service,
                            new_security_service,
                            reset_operation=parsed_args.restart_check)

                    is_compatible = check_result[1].get('compatible')
                    # NOTE(gouthamr): We're logging to the console here,
                    # because there's no need to print useful
                    # information beyond the result. Use of error
                    # logging is a hack, since other kinds of logs may
                    # not print to console by default.
                    if is_compatible is None:
                        LOG.error("Security service check has been "
                                  "successfully initiated, please retry "
                                  "after some time.")
                    elif is_compatible:
                        LOG.error(
                            f"Security service "
                            f"{parsed_args.current_security_service} can "
                            f"be replaced with security service "
                            f"{parsed_args.new_security_service} on share "
                            f"network {parsed_args.share_network}.")
                    else:
                        LOG.error(
                            f"Security service "
                            f"{parsed_args.current_security_service} cannot "
                            f"be replaced with security service "
                            f"{parsed_args.new_security_service} on share "
                            f"network {parsed_args.share_network}.")
                else:
                    share_client.share_networks.\
                        update_share_network_security_service(
                            share_network,
                            current_security_service,
                            new_security_service)
            except Exception as e:
                result += 1
                LOG.error(f"Failed to update security service "
                          f"{parsed_args.current_security_service} on "
                          f"share network "
                          f"{parsed_args.share_network}: {e}")

        if result > 0:
            raise exceptions.CommandError(_("One or more of the "
                                          "set operations failed"))


class UnsetShareNetwork(command.Command):
    """Unset a share network property."""
    _description = _("Unset a share network property")

    def get_parser(self, prog_name):
        parser = super(UnsetShareNetwork, self).get_parser(prog_name)
        parser.add_argument(
            "share_network",
            metavar="<share-network>",
            help=_("Name or ID of the share network to unset a property of")
        )
        parser.add_argument(
            "--name",
            action='store_true',
            help=_("Unset share network name."),
        )
        parser.add_argument(
            "--description",
            action='store_true',
            help=_("Unset share network description."),
        )
        parser.add_argument(
            "--security-service",
            metavar="<security-service>",
            help=_("Disassociate a security service from the share network. "
                   "This is only possible with unused share networks."),
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        share_network = oscutils.find_resource(
            share_client.share_networks,
            parsed_args.share_network)

        security_service = None
        if parsed_args.security_service:
            security_service = oscutils.find_resource(
                share_client.security_services,
                parsed_args.security_service)

        result = 0
        kwargs = {}
        if parsed_args.name:
            # the SDK unsets name if it is an empty string
            kwargs['name'] = ''
        if parsed_args.description:
            # the SDK unsets description if it is an empty string
            kwargs['description'] = ''
        if kwargs:
            try:
                share_client.share_networks.update(
                    share_network,
                    **kwargs
                )
            except Exception as e:
                result += 1
                LOG.error(f"Failed to unset share network properties "
                          f"{kwargs}: {e}")

        if security_service:
            try:
                share_client.share_networks.remove_security_service(
                    share_network, security_service)
            except Exception as e:
                result += 1
                LOG.error(f"Failed to dissociate security service"
                          f"{parsed_args.security_service} from "
                          f"{parsed_args.share_network}: {e}")

        if result > 0:
            raise exceptions.CommandError(_("One or more of the "
                                          "unset operations failed"))
