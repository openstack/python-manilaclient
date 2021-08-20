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
from osc_lib import utils

from manilaclient import api_versions
from manilaclient.common._i18n import _


class QuotaSet(command.Command):
    """Set quotas for a project or project/user or project/share-type.

    It can be used to set the default class for all projects.
    """

    _description = _("Set Quota for a project, or project/user or "
                     "project/share-type or a class.")

    def get_parser(self, prog_name):
        parser = super(QuotaSet, self).get_parser(prog_name)
        quota_type = parser.add_mutually_exclusive_group()
        parser.add_argument(
            'project',
            metavar='<project/class>',
            help=_("A project (name/ID) or a class (e.g.: default).")
        )
        quota_type.add_argument(
            '--class',
            dest='quota_class',
            action='store_true',
            default=False,
            help=_("Update class quota to all projects. "
                   "Mutually exclusive with '--user' and '--share-type'.")
        )
        quota_type.add_argument(
            '--user',
            metavar='<user>',
            default=None,
            help=_("Name or ID of a user to set the quotas for. "
                   "Mutually exclusive with '--share-type' and '--class'.")
        )
        quota_type.add_argument(
            '--share-type',
            metavar='<share-type>',
            type=str,
            default=None,
            help=_("Name or ID of a share type to set the quotas for. "
                   "Mutually exclusive with '--user' and '--class'. "
                   "Available only for microversion >= 2.39")
        )
        parser.add_argument(
            '--shares',
            metavar='<shares>',
            type=int,
            default=None,
            help=_('New value for the "shares" quota.')
        )
        parser.add_argument(
            '--snapshots',
            metavar='<snapshots>',
            type=int,
            default=None,
            help=_('New value for the "snapshots" quota.')
        )
        parser.add_argument(
            '--gigabytes',
            metavar='<gigabytes>',
            type=int,
            default=None,
            help=_('New value for the "gigabytes" quota.')
        )
        parser.add_argument(
            '--snapshot-gigabytes',
            metavar='<snapshot-gigabytes>',
            type=int,
            default=None,
            help=_('New value for the "snapshot-gigabytes" quota.')
        )
        parser.add_argument(
            '--share-networks',
            metavar='<share-networks>',
            type=int,
            default=None,
            help=_('New value for the "share-networks" quota.')
        )
        parser.add_argument(
            '--share-groups',
            metavar='<share-groups>',
            type=int,
            default=None,
            help=_('New value for the "share-groups" quota. '
                   'Available only for microversion >= 2.40')
        )
        parser.add_argument(
            '--share-group-snapshots',
            metavar='<share-group-snapshots>',
            type=int,
            default=None,
            help=_('New value for the "share-group-snapshots" quota. '
                   'Available only for microversion >= 2.40')
        )
        parser.add_argument(
            '--share-replicas',
            metavar='<share-replicas>',
            type=int,
            default=None,
            help=_("Number of share replicas. "
                   "Available only for microversion >= 2.53")
        )
        parser.add_argument(
            '--replica-gigabytes',
            metavar='<replica-gigabytes>',
            type=int,
            default=None,
            help=_("Capacity of share replicas in total. "
                   "Available only for microversion >= 2.53")
        )
        parser.add_argument(
            '--per-share-gigabytes',
            metavar='<per-share-gigabytes>',
            type=int,
            default=None,
            help=_("New value for the 'per-share-gigabytes' quota."
                   "Available only for microversion >= 2.62")
        )
        parser.add_argument(
            '--force',
            dest='force',
            action="store_true",
            default=None,
            help=_('Force update the quota. '
                   'Not applicable for class update.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        user_id = None
        if parsed_args.user:
            user_id = utils.find_resource(
                identity_client.users,
                parsed_args.user).id

        kwargs = {
            "shares": parsed_args.shares,
            "snapshots": parsed_args.snapshots,
            "gigabytes": parsed_args.gigabytes,
            "snapshot_gigabytes": parsed_args.snapshot_gigabytes,
            "share_networks": parsed_args.share_networks,
            "per_share_gigabytes": parsed_args.per_share_gigabytes,
        }

        if parsed_args.share_type is not None:
            if share_client.api_version < api_versions.APIVersion('2.39'):
                raise exceptions.CommandError(_(
                    "'share type' quotas are available only starting with "
                    "'2.39' API microversion."))
            kwargs["share_type"] = parsed_args.share_type
        if parsed_args.share_groups is not None:
            if share_client.api_version < api_versions.APIVersion('2.40'):
                raise exceptions.CommandError(_(
                    "'share group' quotas are available only starting with "
                    "'2.40' API microversion."))
            kwargs["share_groups"] = parsed_args.share_groups
        if parsed_args.share_group_snapshots is not None:
            if share_client.api_version < api_versions.APIVersion('2.40'):
                raise exceptions.CommandError(_(
                    "'share group snapshots' quotas are available only "
                    "starting with '2.40' API microversion."))
            kwargs["share_group_snapshots"] = parsed_args.share_group_snapshots
        if parsed_args.share_replicas is not None:
            if share_client.api_version < api_versions.APIVersion('2.53'):
                raise exceptions.CommandError(_(
                    "setting the number of 'share replicas' is available only "
                    "starting with API microversion '2.53'."))
            kwargs["share_replicas"] = parsed_args.share_replicas
        if parsed_args.replica_gigabytes is not None:
            if share_client.api_version < api_versions.APIVersion('2.53'):
                raise exceptions.CommandError(_(
                    "setting the capacity of share replicas in total "
                    "is available only starting with API microversion '2.53'.")
                )
            kwargs["replica_gigabytes"] = parsed_args.replica_gigabytes
        if parsed_args.per_share_gigabytes is not None:
            if share_client.api_version < api_versions.APIVersion('2.62'):
                raise exceptions.CommandError(_(
                    "'per share gigabytes' quotas are available only "
                    "starting with '2.62' API microversion.")
                )
            kwargs["per_share_gigabytes"] = parsed_args.per_share_gigabytes

        if all(value is None for value in kwargs.values()):
            raise exceptions.CommandError(_(
                "Nothing to set. "
                "New quota must be specified to at least one of the following "
                "resources: 'shares', 'snapshots', 'gigabytes', "
                "'snapshot-gigabytes', 'share-networks', 'share-type', "
                "'share-groups', 'share-group-snapshots', 'share-replicas', "
                "'replica-gigabytes', 'per-share-gigabytes'"))

        if parsed_args.quota_class:
            kwargs.update({
                "class_name": parsed_args.project,
            })
            try:
                share_client.quota_classes.update(**kwargs)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Failed to set quotas for %s class: '%s'")
                    % (parsed_args.project, e))
        else:
            project_id = utils.find_resource(
                identity_client.projects,
                parsed_args.project).id

            kwargs.update({
                "tenant_id": project_id,
                "force": parsed_args.force,
                "user_id": user_id
            })

            try:
                share_client.quotas.update(**kwargs)
            except Exception as e:
                raise exceptions.CommandError(_(
                    "Failed to set quotas for project '%s' : '%s'")
                    % (parsed_args.project, e))


class QuotaShow(command.ShowOne):
    """List the quotas for a project or project/user or project/share-type."""
    _description = _("Show Quota")

    def get_parser(self, prog_name):
        parser = super(QuotaShow, self).get_parser(prog_name)
        quota_type = parser.add_mutually_exclusive_group()
        parser.add_argument(
            'project',
            metavar='<project>',
            help=_('Name or ID of the project to list quotas for.')
        )
        quota_type.add_argument(
            '--user',
            metavar='<user>',
            default=None,
            help=_("Name or ID of user to list the quotas for. Optional. "
                   "Mutually exclusive with '--share-type'.")
        )
        quota_type.add_argument(
            '--share-type',
            metavar='<share-type>',
            type=str,
            default=None,
            help=_("Name or ID of a share type to list the quotas for. "
                   "Optional. "
                   "Mutually exclusive with '--user'. "
                   "Available only for microversion >= 2.39")
        )
        parser.add_argument(
            '--detail',
            action='store_true',
            default=False,
            help=_('Optional flag to indicate whether to show quota in detail.'
                   ' Default false, available only for microversion >= 2.25.')
        )
        parser.add_argument(
            '--defaults',
            action='store_true',
            default=False,
            help=_('Show the default quotas for the project.')
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        user_id = None
        if parsed_args.user:
            user_id = utils.find_resource(
                identity_client.users,
                parsed_args.user).id

        project_id = utils.find_resource(
            identity_client.projects,
            parsed_args.project).id

        quotas = {}
        if parsed_args.defaults:
            quotas = share_client.quotas.defaults(project_id)
        else:
            kwargs = {
                "tenant_id": project_id,
                "user_id": user_id,
                "detail": parsed_args.detail,
            }
            if parsed_args.share_type is not None:
                if share_client.api_version < api_versions.APIVersion("2.39"):
                    raise exceptions.CommandError(_(
                        "'share type' quotas are available only starting with "
                        "'2.39' API microversion."))
                kwargs["share_type"] = parsed_args.share_type

            quotas = share_client.quotas.get(**kwargs)

        printable_quotas = {}
        for quota_k, quota_v in sorted(quotas.to_dict().items()):
            if isinstance(quota_v, dict):
                quota_v = '\n'.join(
                    ['%s = %s' % (k, v) for k, v in sorted(quota_v.items())])
            printable_quotas[quota_k] = quota_v

        return self.dict2columns(printable_quotas)


class QuotaDelete(command.Command):
    """Delete quota for project/user or project/share-type.

    The quota will revert back to default.
    """

    _description = _("Delete Quota")

    def get_parser(self, prog_name):
        parser = super(QuotaDelete, self).get_parser(prog_name)
        quota_type = parser.add_mutually_exclusive_group()
        parser.add_argument(
            'project',
            metavar='<project>',
            help=_('Name or ID of the project to delete quotas for.')
        )
        quota_type.add_argument(
            '--user',
            metavar='<user>',
            default=None,
            help=_("Name or ID of user to delete the quotas for. Optional. "
                   "Mutually exclusive with '--share-type'.")
        )
        quota_type.add_argument(
            '--share-type',
            metavar='<share-type>',
            type=str,
            default=None,
            help=_("Name or ID of a share type to delete the quotas for. "
                   "Optional. "
                   "Mutually exclusive with '--user'. "
                   "Available only for microversion >= 2.39")
        )
        return parser

    def take_action(self, parsed_args):
        share_client = self.app.client_manager.share
        identity_client = self.app.client_manager.identity

        user_id = None
        if parsed_args.user:
            user_id = utils.find_resource(
                identity_client.users,
                parsed_args.user).id

        project_id = utils.find_resource(
            identity_client.projects,
            parsed_args.project).id

        kwargs = {
            "tenant_id": project_id,
            "user_id": user_id
        }
        if parsed_args.share_type:
            if share_client.api_version < api_versions.APIVersion("2.39"):
                raise exceptions.CommandError(_(
                    "'share type' quotas are available only starting with "
                    "API microversion '2.39'."))
            kwargs["share_type"] = parsed_args.share_type

        share_client.quotas.delete(**kwargs)
