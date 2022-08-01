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

LOG = logging.getLogger(__name__)


class CreateShareSecurityService(command.ShowOne):
    """Create security service used by project."""
    _description = _("Create security service used by project.")

    def get_parser(self, prog_name):
        parser = super(CreateShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            'type',
            metavar='<type>',
            default=None,
            choices=['ldap', 'kerberos', 'active_directory'],
            help=_("Security service type. Possible options are: "
                   "'ldap', 'kerberos', 'active_directory'.")
        )
        parser.add_argument(
            '--dns-ip',
            metavar='<dns-ip>',
            default=None,
            help=_("DNS IP address of the security service used "
                   "inside project's network.")
        )
        parser.add_argument(
            '--ou',
            metavar='<ou>',
            default=None,
            help=_("Security service OU (Organizational Unit). "
                   "Available only for microversion >= 2.44.")
        )
        parser.add_argument(
            '--server',
            metavar='<server>',
            default=None,
            help=_("Security service IP address or hostname.")
        )
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            default=None,
            help=_("Security service domain.")
        )
        parser.add_argument(
            '--user',
            metavar='<user',
            default=None,
            help=_("Security service user or group used by project.")
        )
        parser.add_argument(
            '--password',
            metavar='<password>',
            default=None,
            help=_("Password used by user.")
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help=_("Security service name.")
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_("Security service description.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        kwargs = {
            'dns_ip': parsed_args.dns_ip,
            'server': parsed_args.server,
            'domain': parsed_args.domain,
            'user': parsed_args.user,
            'password': parsed_args.password,
            'name': parsed_args.name,
            'description': parsed_args.description,
        }

        if share_client.api_version >= api_versions.APIVersion("2.44"):
            kwargs['ou'] = parsed_args.ou

        elif parsed_args.ou:
            raise exceptions.CommandError(
                "Defining a security service Organizational Unit is "
                "available only for microversion >= 2.44")

        security_service = share_client.security_services.create(
            parsed_args.type, **kwargs)

        return self.dict2columns(security_service._info)


class DeleteShareSecurityService(command.Command):
    """Delete one or more security services."""
    _description = _("Delete one or more security services.")

    def get_parser(self, prog_name):
        parser = super(DeleteShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            'security_service',
            metavar='<security-service>',
            nargs="+",
            help=_("Name or ID of the security service(s) to delete.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        result = 0

        for security_service in parsed_args.security_service:
            try:
                security_service_obj = oscutils.find_resource(
                    share_client.security_services,
                    security_service)
                share_client.security_services.delete(
                    security_service_obj)

            except Exception as e:
                result += 1
                LOG.error(f"Failed to delete security service with "
                          f"name or ID {security_service}: {e}")

        if result > 0:
            total = len(parsed_args.security_service)
            msg = (f"{result} of {total} security services failed "
                   f"to be deleted.")
            raise exceptions.CommandError(msg)


class ShowShareSecurityService(command.ShowOne):
    """Show security service."""
    _description = _("Show security service.")

    def get_parser(self, prog_name):
        parser = super(ShowShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            'security_service',
            metavar='<security-service>',
            help=_("Security service name or ID to show.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        security_service = oscutils.find_resource(
            share_client.security_services,
            parsed_args.security_service)

        data = security_service._info
        if parsed_args.formatter == 'table':
            if 'share_networks' in data.keys():
                data['share_networks'] = "\n".join(
                    data['share_networks'])

        return self.dict2columns(data)


class SetShareSecurityService(command.Command):
    """Set security service."""
    _description = _("Set security service.")

    def get_parser(self, prog_name):
        parser = super(SetShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            'security_service',
            metavar='<security-service>',
            help=_("Security service name or ID.")
        )
        parser.add_argument(
            '--dns-ip',
            metavar='<dns-ip>',
            default=None,
            help=_("Set DNS IP address used inside project's network.")
        )
        parser.add_argument(
            '--ou',
            metavar='<ou>',
            default=None,
            help=_("Set security service OU (Organizational Unit). "
                   "Available only for microversion >= 2.44.")
        )
        parser.add_argument(
            '--server',
            metavar='<server>',
            default=None,
            help=_("Set security service IP address or hostname.")
        )
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            default=None,
            help=_("Set security service domain.")
        )
        parser.add_argument(
            '--user',
            metavar='<user',
            default=None,
            help=_("Set security service user or group used by project.")
        )
        parser.add_argument(
            '--password',
            metavar='<password>',
            default=None,
            help=_("Set password used by user.")
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help=_("Set security service name.")
        )
        parser.add_argument(
            '--description',
            metavar='<description>',
            default=None,
            help=_("Set security service description.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        security_service = oscutils.find_resource(
            share_client.security_services,
            parsed_args.security_service)

        kwargs = {
            'dns_ip': parsed_args.dns_ip,
            'server': parsed_args.server,
            'domain': parsed_args.domain,
            'user': parsed_args.user,
            'password': parsed_args.password,
            'name': parsed_args.name,
            'description': parsed_args.description,
        }

        if share_client.api_version >= api_versions.APIVersion("2.44"):
            kwargs['ou'] = parsed_args.ou

        elif parsed_args.ou:
            raise exceptions.CommandError(_(
                "Setting a security service Organizational Unit is "
                "available only for microversion >= 2.44"))
        try:
            security_service.update(**kwargs)
        except Exception as e:
            raise exceptions.CommandError(
                f"One or more set operations failed: {e}")


class UnsetShareSecurityService(command.Command):
    """Unset security service."""
    _description = _("Unset security service.")

    def get_parser(self, prog_name):
        parser = super(UnsetShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            'security_service',
            metavar='<security-service>',
            help=_("Security service name or ID.")
        )
        parser.add_argument(
            '--dns-ip',
            action='store_true',
            help=_("Unset DNS IP address used inside project's network.")
        )
        parser.add_argument(
            '--ou',
            action='store_true',
            help=_("Unset security service OU (Organizational Unit). "
                   "Available only for microversion >= 2.44.")
        )
        parser.add_argument(
            '--server',
            action='store_true',
            help=_("Unset security service IP address or hostname.")
        )
        parser.add_argument(
            '--domain',
            action='store_true',
            help=_("Unset security service domain.")
        )
        parser.add_argument(
            '--user',
            action='store_true',
            help=_("Unset security service user or group used by project.")
        )
        parser.add_argument(
            '--password',
            action='store_true',
            help=_("Unset password used by user.")
        )
        parser.add_argument(
            '--name',
            action='store_true',
            help=_("Unset security service name.")
        )
        parser.add_argument(
            '--description',
            action='store_true',
            help=_("Unset security service description.")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        security_service = oscutils.find_resource(
            share_client.security_services,
            parsed_args.security_service)

        kwargs = {}
        args = ['dns_ip', 'server', 'domain', 'user', 'password',
                'name', 'description']
        for arg in args:
            if getattr(parsed_args, arg):
                # the SDK unsets a value if it is an empty string
                kwargs[arg] = ''

        if (parsed_args.ou and
                share_client.api_version >= api_versions.APIVersion("2.44")):
            # the SDK unsets a value if it is an empty string
            kwargs['ou'] = ''

        elif parsed_args.ou:
            raise exceptions.CommandError(_(
                "Unsetting a security service Organizational Unit is "
                "available only for microversion >= 2.44"))
        try:
            security_service.update(**kwargs)
        except Exception as e:
            raise exceptions.CommandError(
                f"One or more unset operations failed: {e}")


class ListShareSecurityService(command.Lister):
    """List security services."""
    _description = _("List security services.")

    def get_parser(self, prog_name):
        parser = super(ListShareSecurityService, self).get_parser(prog_name)
        parser.add_argument(
            '--all-projects',
            action='store_true',
            help=_("Display information from all projects (Admin only).")
        )
        parser.add_argument(
            '--share-network',
            metavar='<share-network>',
            default=None,
            help=_("Filter results by share network name or ID.")
        )
        parser.add_argument(
            '--status',
            metavar='<status>',
            default=None,
            help=_("Filter results by status.")
        )
        parser.add_argument(
            '--name',
            metavar='<name>',
            default=None,
            help=_("Filter results by security service name.")
        )
        parser.add_argument(
            '--type',
            metavar='<type>',
            default=None,
            help=_("Filter results by security service type.")
        )
        parser.add_argument(
            '--user',
            metavar='<user',
            default=None,
            help=_("Filter results by security service user or group "
                   "used by project.")
        )
        parser.add_argument(
            '--dns-ip',
            metavar='<dns-ip>',
            default=None,
            help=_("Filter results by DNS IP address used inside "
                   "project's network.")
        )
        parser.add_argument(
            '--ou',
            metavar='<ou>',
            default=None,
            help=_("Filter results by security service OU "
                   "(Organizational Unit). "
                   "Available only for microversion >= 2.44.")
        )
        parser.add_argument(
            '--server',
            metavar='<server>',
            default=None,
            help=_("Filter results by security service IP "
                   "address or hostname.")
        )
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            default=None,
            help=_("Filter results by security service domain.")
        )
        parser.add_argument(
            '--detail',
            action='store_true',
            help=_("Show detailed information about filtered "
                   "security services.")
        )
        parser.add_argument(
            "--limit",
            metavar="<num-security-services>",
            type=int,
            default=None,
            action=parseractions.NonNegativeAction,
            help=_("Limit the number of security services returned")
        )
        parser.add_argument(
            "--marker",
            metavar="<security-service>",
            help=_("The last security service ID of the previous page")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share

        columns = ['ID', 'Name', 'Status', 'Type']

        if parsed_args.all_projects:
            columns.append('Project ID')

        if parsed_args.detail:
            columns.append('Share Networks')

        search_opts = {
            'all_tenants': parsed_args.all_projects,
            'status': parsed_args.status,
            'name': parsed_args.name,
            'type': parsed_args.type,
            'user': parsed_args.user,
            'dns_ip': parsed_args.dns_ip,
            'server': parsed_args.server,
            'domain': parsed_args.domain,
            'offset': parsed_args.marker,
            'limit': parsed_args.limit,
        }

        if (parsed_args.ou and
                share_client.api_version >= api_versions.APIVersion("2.44")):
            search_opts['ou'] = parsed_args.ou

        elif parsed_args.ou:
            raise exceptions.CommandError(_(
                "Filtering results by security service Organizational Unit is "
                "available only for microversion >= 2.44"))

        if parsed_args.share_network:
            search_opts['share_network_id'] = oscutils.find_resource(
                share_client.share_networks,
                parsed_args.share_network).id

        data = share_client.security_services.list(
            search_opts=search_opts,
            detailed=parsed_args.detail
        )

        return (
            columns,
            (oscutils.get_item_properties(s, columns) for s in data)
        )
