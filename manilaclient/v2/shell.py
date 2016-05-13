# Copyright 2013 OpenStack LLC.
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

from __future__ import print_function


import os
import sys
import time

from oslo_utils import strutils
import six

from manilaclient import api_versions
from manilaclient.common import constants
from manilaclient import exceptions
from manilaclient.openstack.common.apiclient import utils as apiclient_utils
from manilaclient.openstack.common import cliutils
from manilaclient.v2 import quotas


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while action is performed, periodically printing progress."""
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _find_share(cs, share):
    """Get a share by ID."""
    return apiclient_utils.find_resource(cs.shares, share)


def _transform_export_locations_to_string_view(export_locations):
    export_locations_string_view = ''
    for el in export_locations:
        if hasattr(el, '_info'):
            export_locations_dict = el._info
        else:
            export_locations_dict = el
        for k, v in export_locations_dict.items():
            export_locations_string_view += '\n%(k)s = %(v)s' % {
                'k': k, 'v': v}
    return export_locations_string_view


@api_versions.wraps("1.0", "2.8")
def _print_share(cs, share):
    info = share._info.copy()
    info.pop('links', None)

    # NOTE(vponomaryov): remove deprecated single field 'export_location' and
    # leave only list field 'export_locations'. Also, transform the latter to
    # text with new line separators to make it pretty in CLI.
    # It will look like following:
    # +-------------------+--------------------------------------------+
    # | Property          | Value                                      |
    # +-------------------+--------------------------------------------+
    # | status            | available                                  |
    # | export_locations  | 1.2.3.4:/f/o/o                             |
    # |                   | 5.6.7.8:/b/a/r                             |
    # |                   | 9.10.11.12:/q/u/u/z                        |
    # | id                | d778d2ee-b6bb-4c5f-9f5d-6f3057d549b1       |
    # | size              | 1                                          |
    # | share_proto       | NFS                                        |
    # +-------------------+--------------------------------------------+
    if info.get('export_locations'):
        info.pop('export_location', None)
        info['export_locations'] = "\n".join(info['export_locations'])

    # No need to print both volume_type and share_type to CLI
    if 'volume_type' in info and 'share_type' in info:
        info.pop('volume_type', None)

    cliutils.print_dict(info)


@api_versions.wraps("2.9")  # noqa
def _print_share(cs, share):
    info = share._info.copy()
    info.pop('links', None)

    # NOTE(vponomaryov): remove deprecated single field 'export_location' and
    # leave only list field 'export_locations'. Also, transform the latter to
    # text with new line separators to make it pretty in CLI.
    # It will look like following:
    # +-------------------+--------------------------------------------+
    # | Property          | Value                                      |
    # +-------------------+--------------------------------------------+
    # | status            | available                                  |
    # | export_locations  |                                            |
    # |                   | uuid = FOO-UUID                            |
    # |                   | path = 5.6.7.8:/foo/export/location/path   |
    # |                   |                                            |
    # |                   | uuid = BAR-UUID                            |
    # |                   | path = 5.6.7.8:/bar/export/location/path   |
    # |                   |                                            |
    # | id                | d778d2ee-b6bb-4c5f-9f5d-6f3057d549b1       |
    # | size              | 1                                          |
    # | share_proto       | NFS                                        |
    # +-------------------+--------------------------------------------+
    if info.get('export_locations'):
        info['export_locations'] = (
            _transform_export_locations_to_string_view(
                info['export_locations']))

    # No need to print both volume_type and share_type to CLI
    if 'volume_type' in info and 'share_type' in info:
        info.pop('volume_type', None)

    cliutils.print_dict(info)


def _find_share_instance(cs, instance):
    """Get a share instance by ID."""
    return apiclient_utils.find_resource(cs.share_instances, instance)


@api_versions.wraps("1.0", "2.8")
def _print_share_instance(cs, instance):
    info = instance._info.copy()
    info.pop('links', None)
    cliutils.print_dict(info)


@api_versions.wraps("2.9")  # noqa
def _print_share_instance(cs, instance):
    info = instance._info.copy()
    info.pop('links', None)
    if info.get('export_locations'):
        info['export_locations'] = (
            _transform_export_locations_to_string_view(
                info['export_locations']))
    cliutils.print_dict(info)


def _find_share_replica(cs, replica):
    """Get a replica by ID."""
    return apiclient_utils.find_resource(cs.share_replicas, replica)


def _print_share_replica(cs, replica):
    info = replica._info.copy()
    info.pop('links', None)
    cliutils.print_dict(info)


@api_versions.experimental_api
@api_versions.wraps("2.4")
def _find_consistency_group(cs, consistency_group):
    """Get a consistency group ID."""
    return apiclient_utils.find_resource(cs.consistency_groups,
                                         consistency_group)


def _print_consistency_group(cs, consistency_group):
    info = consistency_group._info.copy()
    info.pop('links', None)

    if info.get('share_types'):
        info['share_types'] = "\n".join(info['share_types'])

    cliutils.print_dict(info)


def _find_cg_snapshot(cs, cg_snapshot):
    """Get a consistency group snapshot by name or ID."""
    return apiclient_utils.find_resource(cs.cg_snapshots, cg_snapshot)


def _print_cg_snapshot(cs, cg_snapshot):
    info = cg_snapshot._info.copy()
    info.pop('links', None)
    cliutils.print_dict(info)


def _find_share_snapshot(cs, snapshot):
    """Get a snapshot by ID."""
    return apiclient_utils.find_resource(cs.share_snapshots, snapshot)


def _print_share_snapshot(cs, snapshot):
    info = snapshot._info.copy()
    info.pop('links', None)
    cliutils.print_dict(info)


def _find_share_network(cs, share_network):
    """Get a share network by ID or name."""
    return apiclient_utils.find_resource(cs.share_networks, share_network)


def _find_security_service(cs, security_service):
    """Get a security service by ID or name."""
    return apiclient_utils.find_resource(cs.security_services,
                                         security_service)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _extract_metadata(args):
    return _extract_key_value_options(args, 'metadata')


def _extract_extra_specs(args):
    return _extract_key_value_options(args, 'extra_specs')


def _extract_key_value_options(args, option_name):
    result_dict = {}
    options = getattr(args, option_name, None)

    if options:
        for option in options:
            # unset doesn't require a val, so we have the if/else
            if '=' in option:
                (key, value) = option.split('=', 1)
            else:
                key = option
                value = None

            result_dict[key] = value
    return result_dict


@api_versions.wraps("2.0")
def do_api_version(cs, args):
    """Display the API version information."""
    columns = ['ID', 'Status', 'Version', 'Min_version']
    column_labels = ['ID', 'Status', 'Version', 'Minimum Version']
    response = cs.services.server_api_version()
    cliutils.print_list(response, columns, field_labels=column_labels)


def do_endpoints(cs, args):
    """Discover endpoints that get returned from the authenticate services."""
    catalog = cs.keystone_client.service_catalog.catalog
    for e in catalog.get('serviceCatalog', catalog.get('catalog')):
        cliutils.print_dict(e['endpoints'][0], e['name'])


def do_credentials(cs, args):
    """Show user credentials returned from auth."""
    catalog = cs.keystone_client.service_catalog.catalog
    cliutils.print_dict(catalog['user'], "User Credentials")
    if not catalog['version'] == 'v3':
        data = catalog['token']
    else:
        data = {
            'issued_at': catalog['issued_at'],
            'expires': catalog['expires_at'],
            'id': catalog['auth_token'],
            'audit_ids': catalog['audit_ids'],
            'tenant': catalog['project'],
        }
    cliutils.print_dict(data, "Token")

_quota_resources = [
    'shares',
    'snapshots',
    'gigabytes',
    'snapshot_gigabytes',
    'share_networks',
]


def _quota_show(quotas):
    quota_dict = {}
    for resource in _quota_resources:
        quota_dict[resource] = getattr(quotas, resource, None)
    cliutils.print_dict(quota_dict)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        # default value of force is None to make sure this client
        # will be compatible with old nova server
        force_update = getattr(args, 'force', None)
        user_id = getattr(args, 'user', None)
        if isinstance(manager, quotas.QuotaSetManager):
            manager.update(identifier, force=force_update, user_id=user_id,
                           **updates)
        else:
            manager.update(identifier, **updates)


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help='ID of tenant to list the quotas for.')
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help='ID of user to list the quotas for.')
def do_quota_show(cs, args):
    """List the quotas for a tenant/user."""
    project_id = cs.keystone_client.project_id
    if not args.tenant:
        _quota_show(cs.quotas.get(project_id, user_id=args.user))
    else:
        _quota_show(cs.quotas.get(args.tenant, user_id=args.user))


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help='ID of tenant to list the default quotas for.')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""
    project_id = cs.keystone_client.project_id
    if not args.tenant:
        _quota_show(cs.quotas.defaults(project_id))
    else:
        _quota_show(cs.quotas.defaults(args.tenant))


@cliutils.arg(
    'tenant',
    metavar='<tenant_id>',
    help='UUID of tenant to set the quotas for.')
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    default=None,
    help='ID of user to set the quotas for.')
@cliutils.arg(
    '--shares',
    metavar='<shares>',
    type=int,
    default=None,
    help='New value for the "shares" quota.')
@cliutils.arg(
    '--snapshots',
    metavar='<snapshots>',
    type=int,
    default=None,
    help='New value for the "snapshots" quota.')
@cliutils.arg(
    '--gigabytes',
    metavar='<gigabytes>',
    type=int,
    default=None,
    help='New value for the "gigabytes" quota.')
@cliutils.arg(
    '--snapshot-gigabytes',
    '--snapshot_gigabytes',  # alias
    metavar='<snapshot_gigabytes>',
    type=int,
    default=None,
    action='single_alias',
    help='New value for the "snapshot_gigabytes" quota.')
@cliutils.arg(
    '--share-networks',
    '--share_networks',
    metavar='<share-networks>',
    type=int,
    default=None,
    action='single_alias',
    help='New value for the "share_networks" quota.')
@cliutils.arg(
    '--force',
    dest='force',
    action="store_true",
    default=None,
    help='Whether force update the quota even if the already used '
         'and reserved exceeds the new quota.')
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user (Admin only)."""

    _quota_update(cs.quotas, args.tenant, args)


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    help='ID of tenant to delete quota for.')
@cliutils.arg(
    '--user',
    metavar='<user-id>',
    help='ID of user to delete quota for.')
def do_quota_delete(cs, args):
    """Delete quota for a tenant/user.

    The quota will revert back to default (Admin only).
    """
    if not args.tenant:
        project_id = cs.keystone_client.project_id
        cs.quotas.delete(project_id, user_id=args.user)
    else:
        cs.quotas.delete(args.tenant, user_id=args.user)


@cliutils.arg(
    'class_name',
    metavar='<class>',
    help='Name of quota class to list the quotas for.')
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@cliutils.arg(
    'class_name',
    metavar='<class-name>',
    help='Name of quota class to set the quotas for.')
@cliutils.arg(
    '--shares',
    metavar='<shares>',
    type=int,
    default=None,
    help='New value for the "shares" quota.')
@cliutils.arg(
    '--snapshots',
    metavar='<snapshots>',
    type=int,
    default=None,
    help='New value for the "snapshots" quota.')
@cliutils.arg(
    '--gigabytes',
    metavar='<gigabytes>',
    type=int,
    default=None,
    help='New value for the "gigabytes" quota.')
@cliutils.arg(
    '--snapshot-gigabytes',
    '--snapshot_gigabytes',  # alias
    metavar='<snapshot_gigabytes>',
    type=int,
    default=None,
    action='single_alias',
    help='New value for the "snapshot_gigabytes" quota.')
@cliutils.arg(
    '--share-networks',
    '--share_networks',  # alias
    metavar='<share-networks>',
    type=int,
    default=None,
    action='single_alias',
    help='New value for the "share_networks" quota.')
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class (Admin only)."""

    _quota_update(cs.quota_classes, args.class_name, args)


def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user."""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    cliutils.print_list(limits, columns)


@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "verb,uri,value"')
def do_rate_limits(cs, args):
    """Print a list of rate limits for a user."""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']

    if args.columns is not None:
        columns = _split_columns(columns=args.columns)

    cliutils.print_list(limits, columns)


@cliutils.arg(
    'share_protocol',
    metavar='<share_protocol>',
    type=str,
    help='Share type (NFS, CIFS, CephFS, GlusterFS or HDFS).')
@cliutils.arg(
    'size',
    metavar='<size>',
    type=int,
    help='Share size in GiB.')
@cliutils.arg(
    '--snapshot-id',
    '--snapshot_id',
    metavar='<snapshot-id>',
    action='single_alias',
    help='Optional snapshot ID to create the share from. (Default=None)',
    default=None)
@cliutils.arg(
    '--name',
    metavar='<name>',
    help='Optional share name. (Default=None)',
    default=None)
@cliutils.arg(
    '--metadata',
    type=str,
    nargs='*',
    metavar='<key=value>',
    help='Metadata key=value pairs (Optional, Default=None).',
    default=None)
@cliutils.arg(
    '--share-network',
    '--share_network',
    metavar='<network-info>',
    action='single_alias',
    help='Optional network info ID or name.',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@cliutils.arg(
    '--share-type', '--share_type', '--volume-type', '--volume_type',
    metavar='<share-type>',
    default=None,
    action='single_alias',
    help='Optional share type. Use of optional volume type is deprecated'
         '(Default=None)')
@cliutils.arg(
    '--public',
    dest='public',
    action='store_true',
    default=False,
    help="Level of visibility for share. Defines whether other tenants are "
         "able to see it or not.")
@cliutils.arg(
    '--availability-zone', '--availability_zone', '--az',
    metavar='<availability-zone>',
    default=None,
    action='single_alias',
    help='Availability zone in which share should be created.')
@cliutils.arg(
    '--consistency-group',
    '--consistency_group',
    '--cg',
    metavar='<consistency-group>',
    action='single_alias',
    help='Optional consistency group name or ID in which to create the share '
         '(Experimental, Default=None).',
    default=None)
@cliutils.service_type('sharev2')
def do_create(cs, args):
    """Creates a new share (NFS, CIFS, CephFS, GlusterFS or HDFS)."""

    share_metadata = None
    if args.metadata is not None:
        share_metadata = _extract_metadata(args)

    consistency_group = None
    if args.consistency_group:
        consistency_group = _find_consistency_group(cs,
                                                    args.consistency_group).id

    share_network = None
    if args.share_network:
        share_network = _find_share_network(cs, args.share_network)
    share = cs.shares.create(args.share_protocol, args.size, args.snapshot_id,
                             args.name, args.description,
                             metadata=share_metadata,
                             share_network=share_network,
                             share_type=args.share_type,
                             is_public=args.public,
                             availability_zone=args.availability_zone,
                             consistency_group_id=consistency_group,)
    _print_share(cs, share)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of share to migrate.')
@cliutils.arg(
    'host',
    metavar='<host#pool>',
    help='Destination host and pool.')
@cliutils.arg(
    '--force-host-copy',
    '--force_host_copy',
    metavar='<True|False>',
    choices=['True', 'False'],
    required=False,
    action='single_alias',
    help='Enables or disables generic host-based force-migration, which '
         'bypasses driver optimizations. Default=False.',
    default=False)
@api_versions.experimental_api
@api_versions.wraps("2.5", "2.14")
def do_migrate(cs, args):
    """(Deprecated) Migrates share to a new host (Admin only, Experimental)."""
    share = _find_share(cs, args.share)
    share.migration_start(args.host, args.force_host_copy, True)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of share to migrate.')
@cliutils.arg(
    'host',
    metavar='<host#pool>',
    help='Destination host and pool.')
@cliutils.arg(
    '--force-host-copy',
    '--force_host_copy',
    metavar='<True|False>',
    choices=['True', 'False'],
    required=False,
    help='Enables or disables generic host-based force-migration, which '
         'bypasses driver optimizations. Default=False.',
    default=False)
@cliutils.arg(
    '--notify',
    metavar='<True|False>',
    choices=['True', 'False'],
    required=False,
    help='Enables or disables notification of data copying completed. '
         'Default=True.',
    default=True)
@api_versions.experimental_api
@api_versions.wraps("2.15")
def do_migration_start(cs, args):
    """Migrates share to a new host (Admin only, Experimental)."""
    share = _find_share(cs, args.share)
    share.migration_start(args.host, args.force_host_copy, args.notify)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of share to complete migration.')
@api_versions.experimental_api
@api_versions.wraps("2.15")
def do_migration_complete(cs, args):
    """Completes migration for a given share (Admin only, Experimental)."""
    share = _find_share(cs, args.share)
    share.migration_complete()


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of share to cancel migration.')
@api_versions.experimental_api
@api_versions.wraps("2.15")
def do_migration_cancel(cs, args):
    """Cancels migration of a given share when copying

    (Admin only, Experimental).
    """
    share = _find_share(cs, args.share)
    share.migration_cancel()


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to modify.')
@cliutils.arg(
    '--task-state',
    '--task_state',
    '--state',
    metavar='<task_state>',
    default='migration_error',
    action='single_alias',
    help=('Indicate which task state to assign the share. Options include '
          'migration_starting, migration_in_progress, migration_completing, '
          'migration_success, migration_error, migration_cancelled, '
          'migration_driver_in_progress, migration_driver_phase1_done, '
          'data_copying_starting, data_copying_in_progress, '
          'data_copying_completing, data_copying_completed, '
          'data_copying_cancelled, data_copying_error. If no value is '
          'provided, migration_error will be used.'))
@api_versions.experimental_api
@api_versions.wraps("2.15")
def do_reset_task_state(cs, args):
    """Explicitly update the task state of a share

    (Admin only, Experimental).
    """
    share = _find_share(cs, args.share)
    share.reset_task_state(args.task_state)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to get share migration progress '
         'information.')
@api_versions.experimental_api
@api_versions.wraps("2.15")
def do_migration_get_progress(cs, args):
    """Gets migration progress of a given share when copying

    (Admin only, Experimental).
    """
    share = _find_share(cs, args.share)
    result = share.migration_get_progress()
    # NOTE(ganso): result[0] is response code, result[1] is dict body
    cliutils.print_dict(result[1])


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to update metadata on.')
@cliutils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'unset'],
    help="Actions: 'set' or 'unset'.")
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    default=[],
    help='Metadata to set or unset (key is only necessary on unset).')
def do_metadata(cs, args):
    """Set or delete metadata on a share."""
    share = _find_share(cs, args.share)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.shares.set_metadata(share, metadata)
    elif args.action == 'unset':
        cs.shares.delete_metadata(share, sorted(list(metadata), reverse=True))


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
def do_metadata_show(cs, args):
    """Show metadata of given share."""
    share = _find_share(cs, args.share)
    metadata = cs.shares.get_metadata(share)._info
    cliutils.print_dict(metadata, 'Property')


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to update metadata on.')
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='+',
    default=[],
    help='Metadata entry or entries to update.')
def do_metadata_update_all(cs, args):
    """Update all metadata of a share."""
    share = _find_share(cs, args.share)
    metadata = _extract_metadata(args)
    metadata = share.update_all_metadata(metadata)._info['metadata']
    cliutils.print_dict(metadata, 'Property')


@api_versions.wraps("2.9")
@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,host,status"')
def do_share_export_location_list(cs, args):
    """List export locations of a given share."""
    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)
    else:
        list_of_keys = [
            'ID',
            'Path',
            'Preferred',
        ]
    share = _find_share(cs, args.share)
    export_locations = cs.share_export_locations.list(share)
    cliutils.print_list(export_locations, list_of_keys)


@api_versions.wraps("2.9")
@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
@cliutils.arg(
    'export_location',
    metavar='<export_location>',
    help='ID of the share export location.')
def do_share_export_location_show(cs, args):
    """Show export location of the share."""
    share = _find_share(cs, args.share)
    export_location = cs.share_export_locations.get(
        share, args.export_location)
    view_data = export_location._info.copy()
    cliutils.print_dict(view_data)


@cliutils.arg(
    'service_host',
    metavar='<service_host>',
    type=str,
    help='manage-share service host: some.host@driver#pool')
@cliutils.arg(
    'protocol',
    metavar='<protocol>',
    type=str,
    help='Protocol of the share to manage, such as NFS or CIFS.')
@cliutils.arg(
    'export_path',
    metavar='<export_path>',
    type=str,
    help='Share export path, NFS share such as: 10.0.0.1:/example_path, '
         'CIFS share such as: \\\\10.0.0.1\\example_cifs_share')
@cliutils.arg(
    '--name',
    metavar='<name>',
    help='Optional share name. (Default=None)',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@cliutils.arg(
    '--share_type', '--share-type',
    metavar='<share-type>',
    default=None,
    action='single_alias',
    help='Optional share type assigned to share. (Default=None)')
@cliutils.arg(
    '--driver_options', '--driver-options',
    type=str,
    nargs='*',
    metavar='<key=value>',
    action='single_alias',
    help='Driver option key=value pairs (Optional, Default=None).',
    default=None)
@cliutils.arg(
    '--public',
    dest='public',
    action='store_true',
    default=False,
    help="Level of visibility for share. Defines whether other tenants are "
         "able to see it or not. Available only for microversion >= 2.8")
def do_manage(cs, args):
    """Manage share not handled by Manila (Admin only)."""
    driver_options = _extract_key_value_options(args, 'driver_options')

    share = cs.shares.manage(
        args.service_host, args.protocol, args.export_path,
        driver_options=driver_options, share_type=args.share_type,
        name=args.name, description=args.description,
        is_public=args.public,
    )

    _print_share(cs, share)


@api_versions.wraps("2.12")
@cliutils.arg(
    'share',
    metavar='<share>',
    type=str,
    help='Name or ID of the share.')
@cliutils.arg(
    'provider_location',
    metavar='<provider_location>',
    type=str,
    help='Provider location of the snapshot on the backend.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    help='Optional snapshot name (Default=None).',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional snapshot description (Default=None).',
    default=None)
@cliutils.arg(
    '--driver_options', '--driver-options',
    type=str,
    nargs='*',
    metavar='<key=value>',
    action='single_alias',
    help='Optional driver options as key=value pairs (Default=None).',
    default=None)
def do_snapshot_manage(cs, args):
    """Manage share snapshot not handled by Manila (Admin only)."""
    share_ref = _find_share(cs, args.share)

    driver_options = _extract_key_value_options(args, 'driver_options')

    share_snapshot = cs.share_snapshots.manage(
        share_ref, args.provider_location,
        driver_options=driver_options,
        name=args.name, description=args.description
    )

    _print_share_snapshot(cs, share_snapshot)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share(s).')
def do_unmanage(cs, args):
    """Unmanage share (Admin only)."""
    share_ref = _find_share(cs, args.share)
    share_ref.unmanage()


@api_versions.wraps("2.12")
@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    nargs='+',
    help='Name or ID of the snapshot(s).')
def do_snapshot_unmanage(cs, args):
    """Unmanage one or more share snapshots (Admin only)."""
    failure_count = 0
    for snapshot in args.snapshot:
        try:
            snapshot_ref = _find_share_snapshot(cs, snapshot)
            snapshot_ref.unmanage_snapshot()
        except Exception as e:
            failure_count += 1
            print("Unmanage for share snapshot %s failed: %s" % (snapshot, e),
                  file=sys.stderr)

    if failure_count == len(args.snapshot):
        raise exceptions.CommandError("Unable to unmanage any of the "
                                      "specified snapshots.")


@cliutils.arg(
    'share',
    metavar='<share>',
    nargs='+',
    help='Name or ID of the share(s).')
@cliutils.arg(
    '--consistency-group',
    '--consistency_group',
    '--cg',
    metavar='<consistency-group>',
    action='single_alias',
    help='Optional consistency group name or ID which contains the share '
         '(Experimental, Default=None).',
    default=None)
@cliutils.service_type('sharev2')
def do_delete(cs, args):
    """Remove one or more shares."""
    failure_count = 0

    for share in args.share:
        try:
            share_ref = _find_share(cs, share)
            if args.consistency_group:
                consistency_group_id = _find_consistency_group(
                    cs, args.consistency_group).id
                share_ref.delete(consistency_group_id=consistency_group_id)
            else:
                share_ref.delete()
        except Exception as e:
            failure_count += 1
            print("Delete for share %s failed: %s" % (share, e),
                  file=sys.stderr)

    if failure_count == len(args.share):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "shares.")


@cliutils.arg(
    'share',
    metavar='<share>',
    nargs='+',
    help='Name or ID of the share(s) to force delete.')
def do_force_delete(cs, args):
    """Attempt force-delete of share, regardless of state (Admin only)."""
    failure_count = 0
    for share in args.share:
        try:
            _find_share(cs, share).force_delete()
        except Exception as e:
            failure_count += 1
            print("Delete for share %s failed: %s" % (share, e),
                  file=sys.stderr)
    if failure_count == len(args.share):
        raise exceptions.CommandError("Unable to force delete any of "
                                      "specified shares.")


@api_versions.wraps("1.0", "2.8")
@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share.')
def do_show(cs, args):
    """Show details about a NAS share."""
    share = _find_share(cs, args.share)
    _print_share(cs, share)


@api_versions.wraps("2.9")  # noqa
@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share.')
def do_show(cs, args):
    """Show details about a NAS share."""
    share = _find_share(cs, args.share)
    export_locations = cs.share_export_locations.list(share)
    share._info['export_locations'] = export_locations
    _print_share(cs, share)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@cliutils.arg(
    'access_type',
    metavar='<access_type>',
    help='Access rule type (only "ip", "user"(user or group), "cert" or '
         '"cephx" are supported).')
@cliutils.arg(
    'access_to',
    metavar='<access_to>',
    help='Value that defines access.')
@cliutils.arg(
    '--access-level',
    '--access_level',  # alias
    metavar='<access_level>',
    type=str,
    default=None,
    choices=['rw', 'ro'],
    action='single_alias',
    help='Share access level ("rw" and "ro" access levels are supported). '
         'Defaults to rw.')
def do_access_allow(cs, args):
    """Allow access to the share."""
    share = _find_share(cs, args.share)
    access = share.allow(args.access_type, args.access_to, args.access_level)
    cliutils.print_dict(access)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@cliutils.arg(
    'id',
    metavar='<id>',
    help='ID of the access rule to be deleted.')
def do_access_deny(cs, args):
    """Deny access to a share."""
    share = _find_share(cs, args.share)
    share.deny(args.id)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "access_type,access_to"')
def do_access_list(cs, args):
    """Show access list for share."""
    list_of_keys = [
        'id', 'access_type', 'access_to', 'access_level', 'state'
    ]

    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)

    share = _find_share(cs, args.share)
    access_list = share.access_list()
    cliutils.print_list(access_list, list_of_keys)


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--name',
    metavar='<name>',
    type=str,
    default=None,
    help='Filter results by name.')
@cliutils.arg(
    '--status',
    metavar='<status>',
    type=str,
    default=None,
    help='Filter results by status.')
@cliutils.arg(
    '--share-server-id',
    '--share-server_id', '--share_server-id', '--share_server_id',  # aliases
    metavar='<share_server_id>',
    type=str,
    default=None,
    action='single_alias',
    help='Filter results by share server ID (Admin only).')
@cliutils.arg(
    '--metadata',
    type=str,
    nargs='*',
    metavar='<key=value>',
    help='Filters results by a metadata key and value. OPTIONAL: Default=None',
    default=None)
@cliutils.arg(
    '--extra-specs',
    '--extra_specs',  # alias
    type=str,
    nargs='*',
    metavar='<key=value>',
    action='single_alias',
    help='Filters results by a extra specs key and value of share type that '
         'was used for share creation. OPTIONAL: Default=None',
    default=None)
@cliutils.arg(
    '--share-type', '--volume-type',
    '--share_type', '--share-type-id', '--volume-type-id',  # aliases
    '--share-type_id', '--share_type-id', '--share_type_id',  # aliases
    '--volume_type', '--volume_type_id',
    metavar='<share_type>',
    type=str,
    default=None,
    action='single_alias',
    help='Filter results by a share type id or name that was used for share '
         'creation.')
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of shares to return. OPTIONAL: Default=None.')
@cliutils.arg(
    '--offset',
    metavar='<offset>',
    type=int,
    default=None,
    help='Set offset to define start point of share listing. '
         'OPTIONAL: Default=None.')
@cliutils.arg(
    '--sort-key',
    '--sort_key',  # alias
    metavar='<sort_key>',
    type=str,
    default=None,
    action='single_alias',
    help='Key to be sorted, available keys are %(keys)s. '
         'OPTIONAL: Default=None.' % {'keys': constants.SHARE_SORT_KEY_VALUES})
@cliutils.arg(
    '--sort-dir',
    '--sort_dir',  # alias
    metavar='<sort_dir>',
    type=str,
    default=None,
    action='single_alias',
    help='Sort direction, available values are %(values)s. '
         'OPTIONAL: Default=None.' % {'values': constants.SORT_DIR_VALUES})
@cliutils.arg(
    '--snapshot',
    metavar='<snapshot>',
    type=str,
    default=None,
    help='Filer results by snapshot name or id, that was used for share.')
@cliutils.arg(
    '--host',
    metavar='<host>',
    default=None,
    help='Filter results by host.')
@cliutils.arg(
    '--share-network',
    '--share_network',  # alias
    metavar='<share_network>',
    type=str,
    default=None,
    action='single_alias',
    help='Filter results by share-network name or id.')
@cliutils.arg(
    '--project-id',
    '--project_id',  # alias
    metavar='<project_id>',
    type=str,
    default=None,
    action='single_alias',
    help="Filter results by project id. Useful with set key '--all-tenants'.")
@cliutils.arg(
    '--public',
    dest='public',
    action='store_true',
    default=False,
    help="Add public shares from all tenants to result.")
@cliutils.arg(
    '--consistency-group',
    '--consistency_group',
    '--cg',
    metavar='<consistency_group>',
    type=str,
    default=None,
    action='single_alias',
    help='Filter results by consistency group name or ID (Experimental, '
         'Default=None).')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "export_location,is public"')
@cliutils.service_type('sharev2')
def do_list(cs, args):
    """List NAS shares with filters."""

    list_of_keys = [
        'ID', 'Name', 'Size', 'Share Proto', 'Status', 'Is Public',
        'Share Type Name', 'Host', 'Availability Zone'
    ]

    columns = args.columns
    if columns is not None:
        list_of_keys = _split_columns(columns=columns)

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    empty_obj = type('Empty', (object,), {'id': None})
    share_type = (_find_share_type(cs, args.share_type)
                  if args.share_type else empty_obj)

    snapshot = (_find_share_snapshot(cs, args.snapshot)
                if args.snapshot else empty_obj)

    share_network = (_find_share_network(cs, args.share_network)
                     if args.share_network else empty_obj)

    consistency_group = None
    if args.consistency_group:
        consistency_group = _find_consistency_group(cs, args.consistency_group)

    search_opts = {
        'offset': args.offset,
        'limit': args.limit,
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'host': args.host,
        'share_network_id': share_network.id,
        'snapshot_id': snapshot.id,
        'share_type_id': share_type.id,
        'metadata': _extract_metadata(args),
        'extra_specs': _extract_extra_specs(args),
        'share_server_id': args.share_server_id,
        'project_id': args.project_id,
        'is_public': args.public,
    }

    if consistency_group:
        search_opts['consistency_group_id'] = consistency_group.id

    shares = cs.shares.list(
        search_opts=search_opts,
        sort_key=args.sort_key,
        sort_dir=args.sort_dir,
    )
    # NOTE(vponomaryov): usage of 'export_location' and
    # 'export_locations' columns may cause scaling issue using API 2.9+ and
    # when lots of shares are returned.
    if (shares and columns is not None and 'export_location' in columns and
            not hasattr(shares[0], 'export_location')):
        # NOTE(vponomaryov): we will get here only using API 2.9+
        for share in shares:
            els_objs = cs.share_export_locations.list(share)
            els = [el.to_dict()['path'] for el in els_objs]
            setattr(share, 'export_locations', els)
            setattr(share, 'export_location', els[0] if els else None)
    cliutils.print_list(shares, list_of_keys)


@cliutils.arg(
    '--share-id',
    '--share_id',  # alias
    metavar='<share_id>',
    default=None,
    action='single_alias',
    help='Filter results by share ID.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,host,status"')
@api_versions.wraps("2.3")
def do_share_instance_list(cs, args):
    """List share instances (Admin only)."""
    share = _find_share(cs, args.share_id) if args.share_id else None

    list_of_keys = [
        'ID', 'Share ID', 'Host', 'Status', 'Availability Zone',
        'Share Network ID', 'Share Server ID'
    ]

    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)

    if share:
        instances = cs.shares.list_instances(share)
    else:
        instances = cs.share_instances.list()

    cliutils.print_list(instances, list_of_keys)


@api_versions.wraps("2.3", "2.8")
@cliutils.arg(
    'instance',
    metavar='<instance>',
    help='Name or ID of the share instance.')
def do_share_instance_show(cs, args):
    """Show details about a share instance."""
    instance = _find_share_instance(cs, args.instance)
    _print_share_instance(cs, instance)


@api_versions.wraps("2.9")  # noqa
@cliutils.arg(
    'instance',
    metavar='<instance>',
    help='Name or ID of the share instance.')
def do_share_instance_show(cs, args):
    """Show details about a share instance (Admin only)."""
    instance = _find_share_instance(cs, args.instance)
    export_locations = cs.share_instance_export_locations.list(instance)
    instance._info['export_locations'] = export_locations
    _print_share_instance(cs, instance)


@cliutils.arg(
    'instance',
    metavar='<instance>',
    nargs='+',
    help='Name or ID of the instance(s) to force delete.')
@api_versions.wraps("2.3")
def do_share_instance_force_delete(cs, args):
    """Force-delete the share instance, regardless of state (Admin only)."""
    failure_count = 0
    for instance in args.instance:
        try:
            _find_share_instance(cs, instance).force_delete()
        except Exception as e:
            failure_count += 1
            print("Delete for share instance %s failed: %s" % (instance, e),
                  file=sys.stderr)
    if failure_count == len(args.instance):
        raise exceptions.CommandError("Unable to force delete any of "
                                      "specified share instances.")


@cliutils.arg(
    'instance',
    metavar='<instance>',
    help='Name or ID of the share instance to modify.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the instance. Options include '
          'available, error, creating, deleting, error_deleting. If no '
          'state is provided, available will be used.'))
@api_versions.wraps("2.3")
def do_share_instance_reset_state(cs, args):
    """Explicitly update the state of a share instance (Admin only)."""
    instance = _find_share_instance(cs, args.instance)
    instance.reset_state(args.state)


@api_versions.wraps("2.9")
@cliutils.arg(
    'instance',
    metavar='<instance>',
    help='Name or ID of the share instance.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,host,status"')
def do_share_instance_export_location_list(cs, args):
    """List export locations of a given share instance."""
    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)
    else:
        list_of_keys = [
            'ID',
            'Path',
            'Is Admin only',
            'Preferred',
        ]
    instance = _find_share_instance(cs, args.instance)
    export_locations = cs.share_instance_export_locations.list(instance)
    cliutils.print_list(export_locations, list_of_keys)


@api_versions.wraps("2.9")
@cliutils.arg(
    'instance',
    metavar='<instance>',
    help='Name or ID of the share instance.')
@cliutils.arg(
    'export_location',
    metavar='<export_location>',
    help='ID of the share instance export location.')
def do_share_instance_export_location_show(cs, args):
    """Show export location for the share instance."""
    instance = _find_share_instance(cs, args.instance)
    export_location = cs.share_instance_export_locations.get(
        instance, args.export_location)
    view_data = export_location._info.copy()
    cliutils.print_dict(view_data)


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Filter results by name.')
@cliutils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status.')
@cliutils.arg(
    '--share-id',
    '--share_id',  # alias
    metavar='<share_id>',
    default=None,
    action='single_alias',
    help='Filter results by source share ID.')
@cliutils.arg(
    '--usage',
    dest='usage',
    metavar='any|used|unused',
    nargs='?',
    type=str,
    const='any',
    default=None,
    choices=['any', 'used', 'unused', ],
    help='Either filter or not snapshots by its usage. OPTIONAL: Default=any.')
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of share snapshots to return. '
         'OPTIONAL: Default=None.')
@cliutils.arg(
    '--offset',
    metavar='<offset>',
    type=int,
    default=None,
    help='Set offset to define start point of share snapshots listing. '
         'OPTIONAL: Default=None.')
@cliutils.arg(
    '--sort-key',
    '--sort_key',  # alias
    metavar='<sort_key>',
    type=str,
    default=None,
    action='single_alias',
    help='Key to be sorted, available keys are %(keys)s. '
         'Default=None.' % {'keys': constants.SNAPSHOT_SORT_KEY_VALUES})
@cliutils.arg(
    '--sort-dir',
    '--sort_dir',  # alias
    metavar='<sort_dir>',
    type=str,
    default=None,
    action='single_alias',
    help='Sort direction, available values are %(values)s. '
         'OPTIONAL: Default=None.' % {'values': constants.SORT_DIR_VALUES})
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
def do_snapshot_list(cs, args):
    """List all the snapshots."""
    list_of_keys = [
        'ID', 'Share ID', 'Status', 'Name', 'Share Size',
    ]

    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    empty_obj = type('Empty', (object,), {'id': None})
    share = _find_share(cs, args.share_id) if args.share_id else empty_obj
    search_opts = {
        'offset': args.offset,
        'limit': args.limit,
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'share_id': share.id,
        'usage': args.usage,
    }
    snapshots = cs.share_snapshots.list(
        search_opts=search_opts,
        sort_key=args.sort_key,
        sort_dir=args.sort_dir,
    )
    cliutils.print_list(snapshots, list_of_keys)


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot.')
def do_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    _print_share_snapshot(cs, snapshot)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to snapshot.')
@cliutils.arg(
    '--force',
    metavar='<True|False>',
    help='Optional flag to indicate whether '
    'to snapshot a share even if it\'s busy. '
    '(Default=False)',
    default=False)
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Optional snapshot name. (Default=None)')
@cliutils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help='Optional snapshot description. (Default=None)')
def do_snapshot_create(cs, args):
    """Add a new snapshot."""
    share = _find_share(cs, args.share)
    snapshot = cs.share_snapshots.create(share,
                                         args.force,
                                         args.name,
                                         args.description)
    _print_share_snapshot(cs, snapshot)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to rename.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='New name for the share.')
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@cliutils.arg(
    '--is-public',
    '--is_public',  # alias
    metavar='<is_public>',
    default=None,
    type=str,
    action="single_alias",
    help='Public share is visible for all tenants.')
def do_update(cs, args):
    """Rename a share."""
    kwargs = {}

    if args.name is not None:
        kwargs['display_name'] = args.name
    if args.description is not None:
        kwargs['display_description'] = args.description
    if args.is_public is not None:
        kwargs['is_public'] = strutils.bool_from_string(args.is_public,
                                                        strict=True)
    if not kwargs:
        msg = "Must supply name, description or is_public value."
        raise exceptions.CommandError(msg)
    _find_share(cs, args.share).update(**kwargs)


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to rename.')
@cliutils.arg(
    'name',
    nargs='?',
    metavar='<name>',
    help='New name for the snapshot.')
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional snapshot description. (Default=None)',
    default=None)
def do_snapshot_rename(cs, args):
    """Rename a snapshot."""
    kwargs = {}

    if args.name is not None:
        kwargs['display_name'] = args.name
    if args.description is not None:
        kwargs['display_description'] = args.description
    if not kwargs:
        msg = "Must supply either name or description."
        raise exceptions.CommandError(msg)
    _find_share_snapshot(cs, args.snapshot).update(**kwargs)


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to delete.')
def do_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.delete()


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to force delete.')
def do_snapshot_force_delete(cs, args):
    """Attempt force-delete of snapshot, regardless of state (Admin only)."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.force_delete()


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to modify.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the snapshot. '
          'Options include available, error, creating, deleting, '
          'error_deleting. If no state is provided, '
          'available will be used.'))
def do_snapshot_reset_state(cs, args):
    """Explicitly update the state of a snapshot (Admin only)."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.reset_state(args.state)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to modify.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the share. Options include '
          'available, error, creating, deleting, error_deleting. If no '
          'state is provided, available will be used.'))
def do_reset_state(cs, args):
    """Explicitly update the state of a share (Admin only)."""
    share = _find_share(cs, args.share)
    share.reset_state(args.state)


@cliutils.arg(
    '--nova-net-id',
    '--nova-net_id', '--nova_net_id', '--nova_net-id',  # aliases
    metavar='<nova-net-id>',
    default=None,
    action='single_alias',
    help="Nova net ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-net-id',
    '--neutron-net_id', '--neutron_net_id', '--neutron_net-id',
    metavar='<neutron-net-id>',
    default=None,
    action='single_alias',
    help="Neutron network ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-subnet-id',
    '--neutron-subnet_id', '--neutron_subnet_id', '--neutron_subnet-id',
    metavar='<neutron-subnet-id>',
    default=None,
    action='single_alias',
    help="Neutron subnet ID. Used to set up network for share servers. "
         "This subnet should belong to specified neutron network.")
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Share network name.")
@cliutils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Share network description.")
def do_share_network_create(cs, args):
    """Create description for network used by the tenant."""
    values = dict(
        neutron_net_id=args.neutron_net_id,
        neutron_subnet_id=args.neutron_subnet_id,
        nova_net_id=args.nova_net_id,
        name=args.name,
        description=args.description)
    share_network = cs.share_networks.create(**values)
    info = share_network._info.copy()
    cliutils.print_dict(info)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of share network to update.')
@cliutils.arg(
    '--nova-net-id',
    '--nova-net_id', '--nova_net_id', '--nova_net-id',  # aliases
    metavar='<nova-net-id>',
    default=None,
    action='single_alias',
    help="Nova net ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-net-id',
    '--neutron-net_id', '--neutron_net_id', '--neutron_net-id',
    metavar='<neutron-net-id>',
    default=None,
    action='single_alias',
    help="Neutron network ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-subnet-id',
    '--neutron-subnet_id', '--neutron_subnet_id', '--neutron_subnet-id',
    metavar='<neutron-subnet-id>',
    default=None,
    action='single_alias',
    help="Neutron subnet ID. Used to set up network for share servers. "
         "This subnet should belong to specified neutron network.")
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Share network name.")
@cliutils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Share network description.")
def do_share_network_update(cs, args):
    """Update share network data."""
    values = dict(
        neutron_net_id=args.neutron_net_id,
        neutron_subnet_id=args.neutron_subnet_id,
        nova_net_id=args.nova_net_id,
        name=args.name,
        description=args.description)
    share_network = _find_share_network(
        cs, args.share_network).update(**values)
    info = share_network._info.copy()
    cliutils.print_dict(info)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of the share network to show.')
def do_share_network_show(cs, args):
    """Get a description for network used by the tenant."""
    share_network = _find_share_network(cs, args.share_network)
    info = share_network._info.copy()
    cliutils.print_dict(info)


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--project-id',
    '--project_id',  # alias
    metavar='<project_id>',
    action='single_alias',
    default=None,
    help='Filter results by project ID.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Filter results by name.')
@cliutils.arg(
    '--created-since',
    '--created_since',  # alias
    metavar='<created_since>',
    action='single_alias',
    default=None,
    help='''Return only share networks created since given date. '''
         '''The date is in the format 'yyyy-mm-dd'.''')
@cliutils.arg(
    '--created-before',
    '--created_before',  # alias
    metavar='<created_before>',
    action='single_alias',
    default=None,
    help='''Return only share networks created until given date. '''
         '''The date is in the format 'yyyy-mm-dd'.''')
@cliutils.arg(
    '--security-service',
    '--security_service',  # alias
    metavar='<security_service>',
    action='single_alias',
    default=None,
    help='Filter results by attached security service.')
@cliutils.arg(
    '--nova-net-id',
    '--nova_net_id', '--nova_net-id', '--nova-net_id',  # aliases
    metavar='<nova_net_id>',
    action='single_alias',
    default=None,
    help='Filter results by Nova net ID.')
@cliutils.arg(
    '--neutron-net-id',
    '--neutron_net_id', '--neutron_net-id', '--neutron-net_id',  # aliases
    metavar='<neutron_net_id>',
    action='single_alias',
    default=None,
    help='Filter results by neutron net ID.')
@cliutils.arg(
    '--neutron-subnet-id',
    '--neutron_subnet_id', '--neutron-subnet_id',  # aliases
    '--neutron_subnet-id',  # alias
    metavar='<neutron_subnet_id>',
    action='single_alias',
    default=None,
    help='Filter results by neutron subnet ID.')
@cliutils.arg(
    '--network-type',
    '--network_type',  # alias
    metavar='<network_type>',
    action='single_alias',
    default=None,
    help='Filter results by network type.')
@cliutils.arg(
    '--segmentation-id',
    '--segmentation_id',  # alias
    metavar='<segmentation_id>',
    type=int,
    action='single_alias',
    default=None,
    help='Filter results by segmentation ID.')
@cliutils.arg(
    '--cidr',
    metavar='<cidr>',
    default=None,
    help='Filter results by CIDR.')
@cliutils.arg(
    '--ip-version',
    '--ip_version',  # alias
    metavar='<ip_version>',
    type=int,
    action='single_alias',
    default=None,
    help='Filter results by IP version.')
@cliutils.arg(
    '--offset',
    metavar='<offset>',
    type=int,
    default=None,
    help='Start position of share networks listing.')
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Number of share networks to return per request.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id"')
def do_share_network_list(cs, args):
    """Get a list of network info."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'project_id': args.project_id,
        'name': args.name,
        'created_since': args.created_since,
        'created_before': args.created_before,
        'nova_net_id': args.nova_net_id,
        'neutron_net_id': args.neutron_net_id,
        'neutron_subnet_id': args.neutron_subnet_id,
        'network_type': args.network_type,
        'segmentation_id': args.segmentation_id,
        'cidr': args.cidr,
        'ip_version': args.ip_version,
        'offset': args.offset,
        'limit': args.limit,
    }
    if args.security_service:
        search_opts['security_service_id'] = _find_security_service(
            cs, args.security_service).id
    share_networks = cs.share_networks.list(search_opts=search_opts)
    fields = ['id', 'name']

    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    cliutils.print_list(share_networks, fields=fields)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to associate with.')
def do_share_network_security_service_add(cs, args):
    """Associate security service with share network."""
    share_network = _find_share_network(cs, args.share_network)
    security_service = _find_security_service(cs, args.security_service)
    cs.share_networks.add_security_service(share_network, security_service)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to dissociate.')
def do_share_network_security_service_remove(cs, args):
    """Dissociate security service from share network."""
    share_network = _find_share_network(cs, args.share_network)
    security_service = _find_security_service(cs, args.security_service)
    cs.share_networks.remove_security_service(share_network, security_service)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
def do_share_network_security_service_list(cs, args):
    """Get list of security services associated with a given share network."""
    share_network = _find_share_network(cs, args.share_network)
    search_opts = {
        'share_network_id': share_network.id,
    }
    security_services = cs.security_services.list(search_opts=search_opts)
    fields = ['id', 'name', 'status', 'type', ]

    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    cliutils.print_list(security_services, fields=fields)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of share network to be deleted.')
def do_share_network_delete(cs, args):
    """Delete share network."""
    _find_share_network(cs, args.share_network).delete()


@cliutils.arg(
    'type',
    metavar='<type>',
    help="Security service type: 'ldap', 'kerberos' or 'active_directory'.")
@cliutils.arg(
    '--dns-ip',
    metavar='<dns_ip>',
    default=None,
    help="DNS IP address used inside tenant's network.")
@cliutils.arg(
    '--server',
    metavar='<server>',
    default=None,
    help="Security service IP address or hostname.")
@cliutils.arg(
    '--domain',
    metavar='<domain>',
    default=None,
    help="Security service domain.")
@cliutils.arg(
    '--user',
    metavar='<user>',
    default=None,
    help="Security service user or group used by tenant.")
@cliutils.arg(
    '--password',
    metavar='<password>',
    default=None,
    help="Password used by user.")
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Security service name.")
@cliutils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Security service description.")
def do_security_service_create(cs, args):
    """Create security service used by tenant."""
    values = {
        'dns_ip': args.dns_ip,
        'server': args.server,
        'domain': args.domain,
        'user': args.user,
        'password': args.password,
        'name': args.name,
        'description': args.description,
    }
    security_service = cs.security_services.create(args.type, **values)
    info = security_service._info.copy()
    cliutils.print_dict(info)


@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to update.')
@cliutils.arg(
    '--dns-ip',
    metavar='<dns-ip>',
    default=None,
    help="DNS IP address used inside tenant's network.")
@cliutils.arg(
    '--server',
    metavar='<server>',
    default=None,
    help="Security service IP address or hostname.")
@cliutils.arg(
    '--domain',
    metavar='<domain>',
    default=None,
    help="Security service domain.")
@cliutils.arg(
    '--user',
    metavar='<user>',
    default=None,
    help="Security service user or group used by tenant.")
@cliutils.arg(
    '--password',
    metavar='<password>',
    default=None,
    help="Password used by user.")
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Security service name.")
@cliutils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Security service description.")
def do_security_service_update(cs, args):
    """Update security service."""
    values = {
        'dns_ip': args.dns_ip,
        'server': args.server,
        'domain': args.domain,
        'user': args.user,
        'password': args.password,
        'name': args.name,
        'description': args.description,
    }
    security_service = _find_security_service(
        cs, args.security_service).update(**values)
    cliutils.print_dict(security_service._info)


@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to show.')
def do_security_service_show(cs, args):
    """Show security service."""
    security_service = _find_security_service(cs, args.security_service)
    info = security_service._info.copy()
    cliutils.print_dict(info)


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--share-network',
    '--share_network',  # alias
    metavar='<share_network>',
    action='single_alias',
    default=None,
    help='Filter results by share network id or name.')
@cliutils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Filter results by name.')
@cliutils.arg(
    '--type',
    metavar='<type>',
    default=None,
    help='Filter results by type.')
@cliutils.arg(
    '--user',
    metavar='<user>',
    default=None,
    help='Filter results by user or group used by tenant.')
@cliutils.arg(
    '--dns-ip',
    '--dns_ip',  # alias
    metavar='<dns_ip>',
    action='single_alias',
    default=None,
    help="Filter results by DNS IP address used inside tenant's network.")
@cliutils.arg(
    '--server',
    metavar='<server>',
    default=None,
    help="Filter results by security service IP address or hostname.")
@cliutils.arg(
    '--domain',
    metavar='<domain>',
    default=None,
    help="Filter results by domain.")
@cliutils.arg(
    '--detailed',
    dest='detailed',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help="Show detailed information about filtered security services.")
@cliutils.arg(
    '--offset',
    metavar="<offset>",
    default=None,
    help='Start position of security services listing.')
@cliutils.arg(
    '--limit',
    metavar="<limit>",
    default=None,
    help='Number of security services to return per request.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "name,type"')
def do_security_service_list(cs, args):
    """Get a list of security services."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'status': args.status,
        'name': args.name,
        'type': args.type,
        'user': args.user,
        'dns_ip': args.dns_ip,
        'server': args.server,
        'domain': args.domain,
        'offset': args.offset,
        'limit': args.limit,
    }
    if args.share_network:
        search_opts['share_network_id'] = _find_share_network(
            cs, args.share_network).id
    security_services = cs.security_services.list(search_opts=search_opts,
                                                  detailed=args.detailed)
    fields = ['id', 'name', 'status', 'type', ]
    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    if args.detailed:
        fields.append('share_networks')
    cliutils.print_list(security_services, fields=fields)


@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to delete.')
def do_security_service_delete(cs, args):
    """Delete security service."""
    security_service = _find_security_service(cs, args.security_service)
    security_service.delete()


@cliutils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help='Filter results by name of host.')
@cliutils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status.')
@cliutils.arg(
    '--share-network',
    metavar='<share_network>',
    default=None,
    help='Filter results by share network.')
@cliutils.arg(
    '--project-id',
    metavar='<project_id>',
    default=None,
    help='Filter results by project ID.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,host,status"')
def do_share_server_list(cs, args):
    """List all share servers (Admin only)."""
    search_opts = {
        "host": args.host,
        "share_network": args.share_network,
        "status": args.status,
        "project_id": args.project_id,
    }
    fields = [
        "Id",
        "Host",
        "Status",
        "Share Network",
        "Project Id",
        "Updated_at",
    ]

    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    share_servers = cs.share_servers.list(search_opts=search_opts)
    cliutils.print_list(share_servers, fields=fields)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_show(cs, args):
    """Show share server info (Admin only)."""
    share_server = cs.share_servers.get(args.id)
    # All 'backend_details' data already present as separated strings,
    # so remove big dict from view.
    if "backend_details" in share_server._info:
        del share_server._info["backend_details"]
    cliutils.print_dict(share_server._info)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_details(cs, args):
    """Show share server details (Admin only)."""
    details = cs.share_servers.details(args.id)
    cliutils.print_dict(details._info)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_delete(cs, args):
    """Delete share server (Admin only)."""
    cs.share_servers.delete(args.id)


@cliutils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help='Name of host.')
@cliutils.arg(
    '--binary',
    metavar='<binary>',
    default=None,
    help='Service binary.')
@cliutils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default=None,
    help='Filter results by state.')
@cliutils.arg(
    '--zone',
    metavar='<zone>',
    default=None,
    help='Availability zone.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,host"')
def do_service_list(cs, args):
    """List all services (Admin only)."""
    search_opts = {
        'status': args.status,
        'host': args.host,
        'binary': args.binary,
        'zone': args.zone,
        'state': args.state,
    }
    fields = ["Id", "Binary", "Host", "Zone", "Status", "State", "Updated_at"]

    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    services = cs.services.list(search_opts=search_opts)
    cliutils.print_list(services, fields=fields)


@cliutils.arg(
    'host',
    metavar='<hostname>',
    help="Host name as 'example_host@example_backend'.")
@cliutils.arg(
    'binary',
    metavar='<binary>',
    help="Service binary, could be 'manila-share' or 'manila-scheduler'.")
def do_service_enable(cs, args):
    """Enables 'manila-share' or 'manila-scheduler' services (Admin only)."""
    columns = ("Host", "Binary", "Enabled")
    result = cs.services.enable(args.host, args.binary)
    result.enabled = not result.disabled
    cliutils.print_list([result], columns)


@cliutils.arg(
    'host',
    metavar='<hostname>',
    help="Host name as 'example_host@example_backend'.")
@cliutils.arg(
    'binary',
    metavar='<binary>',
    help="Service binary, could be 'manila-share' or 'manila-scheduler'.")
def do_service_disable(cs, args):
    """Disables 'manila-share' or 'manila-scheduler' services (Admin only)."""
    columns = ("Host", "Binary", "Enabled")
    result = cs.services.disable(args.host, args.binary)
    result.enabled = not result.disabled
    cliutils.print_list([result], columns)


def _print_dict(data_dict):
    formatted_data = []

    for date in data_dict:
        formatted_data.append("%s : %s" % (date, data_dict[date]))

    return "\n".join(formatted_data)


def _print_type_extra_specs(share_type):
    try:
        return _print_dict(share_type.get_keys())
    except exceptions.NotFound:
        return None


def _print_type_required_extra_specs(share_type):
    try:
        return _print_dict(share_type.get_required_keys())
    except exceptions.NotFound:
        return "N/A"


def _print_type_optional_extra_specs(share_type):
    try:
        return _print_dict(share_type.get_optional_keys())
    except exceptions.NotFound:
        return "N/A"


def _is_share_type_public(share_type):
    return 'public' if share_type.is_public else 'private'


def _print_share_type_list(stypes, default_share_type=None, columns=None):

    def _is_default(share_type):
        if share_type == default_share_type:
            return 'YES'
        else:
            return '-'

    formatters = {
        'visibility': _is_share_type_public,
        'is_default': _is_default,
        'required_extra_specs': _print_type_required_extra_specs,
        'optional_extra_specs': _print_type_optional_extra_specs,
    }

    for stype in stypes:
        stype = stype.to_dict()
        stype['visibility'] = stype.pop('is_public', 'unknown')

    fields = [
        'ID',
        'Name',
        'visibility',
        'is_default',
        'required_extra_specs',
        'optional_extra_specs',
    ]
    if columns is not None:
        fields = _split_columns(columns=columns, title=False)

    cliutils.print_list(stypes, fields, formatters)


def _print_share_type(stype, default_share_type=None):

    def _is_default(share_type):
        if share_type == default_share_type:
            return 'YES'
        else:
            return '-'

    stype_dict = {
        'ID': stype.id,
        'Name': stype.name,
        'Visibility': _is_share_type_public(stype),
        'is_default': _is_default(stype),
        'required_extra_specs': _print_type_required_extra_specs(stype),
        'optional_extra_specs': _print_type_optional_extra_specs(stype),
    }
    cliutils.print_dict(stype_dict)


def _print_type_and_extra_specs_list(stypes, columns=None):
    formatters = {
        'all_extra_specs': _print_type_extra_specs,
    }
    fields = ['ID', 'Name', 'all_extra_specs']

    if columns is not None:
        fields = _split_columns(columns=columns, title=False)

    cliutils.print_list(stypes, fields, formatters)


def _find_share_type(cs, stype):
    """Get a share type by name or ID."""
    return apiclient_utils.find_resource(cs.share_types, stype)


@cliutils.arg(
    '--all',
    dest='all',
    action='store_true',
    default=False,
    help='Display all share types (Admin only).')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
def do_type_list(cs, args):
    """Print a list of available 'share types'."""
    try:
        default = cs.share_types.get()
    except exceptions.NotFound:
        default = None

    stypes = cs.share_types.list(show_all=args.all)
    _print_share_type_list(stypes, default_share_type=default,
                           columns=args.columns)


@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
def do_extra_specs_list(cs, args):
    """Print a list of current 'share types and extra specs' (Admin Only)."""
    stypes = cs.share_types.list()
    _print_type_and_extra_specs_list(stypes, columns=args.columns)


@cliutils.arg(
    'name',
    metavar='<name>',
    help="Name of the new share type.")
@cliutils.arg(
    'spec_driver_handles_share_servers',
    metavar='<spec_driver_handles_share_servers>',
    type=str,
    help="Required extra specification. "
         "Valid values are 'true'/'1' and 'false'/'0'")
@cliutils.arg(
    '--snapshot_support',
    '--snapshot-support',
    metavar='<snapshot_support>',
    action='single_alias',
    help="Boolean extra spec that used for filtering of back ends by their "
         "capability to create share snapshots. (Default is True).")
@cliutils.arg(
    '--is_public',
    '--is-public',
    metavar='<is_public>',
    action='single_alias',
    help="Make type accessible to the public (default true).")
def do_type_create(cs, args):
    """Create a new share type (Admin only)."""
    kwargs = {
        "name": args.name,
        "is_public": strutils.bool_from_string(args.is_public, default=True),
    }
    try:
        kwargs['spec_driver_handles_share_servers'] = (
            strutils.bool_from_string(
                args.spec_driver_handles_share_servers, strict=True))
    except ValueError as e:
        msg = ("Argument spec_driver_handles_share_servers "
               "argument is not valid: %s" % six.text_type(e))
        raise exceptions.CommandError(msg)
    try:
        if args.snapshot_support:
            kwargs['spec_snapshot_support'] = strutils.bool_from_string(
                args.snapshot_support, strict=True)
    except ValueError as e:
        msg = ("Argument 'snapshot_support' is of boolean type and has "
               "invalid value: %s" % six.text_type(e))
        raise exceptions.CommandError(msg)

    stype = cs.share_types.create(**kwargs)
    _print_share_type(stype)


@cliutils.arg(
    'id',
    metavar='<id>',
    help="Name or ID of the share type to delete.")
def do_type_delete(cs, args):
    """Delete a specific share type (Admin only)."""
    share_type = _find_share_type(cs, args.id)
    cs.share_types.delete(share_type)


@cliutils.arg(
    'stype',
    metavar='<stype>',
    help="Name or ID of the share type.")
@cliutils.arg(
    'action',
    metavar='<action>',
    choices=['set', 'unset'],
    help="Actions: 'set' or 'unset'.")
@cliutils.arg(
    'metadata',
    metavar='<key=value>',
    nargs='*',
    default=None,
    help='Extra_specs to set or unset (key is only necessary on unset).')
def do_type_key(cs, args):
    """Set or unset extra_spec for a share type (Admin only)."""
    stype = _find_share_type(cs, args.stype)

    if args.metadata is not None:
        keypair = _extract_metadata(args)

        if args.action == 'set':
            stype.set_keys(keypair)
        elif args.action == 'unset':
            stype.unset_keys(list(keypair))


@cliutils.arg(
    '--host',
    metavar='<host>',
    type=str,
    default='.*',
    help='Filter results by host name.  Regular expressions are supported.')
@cliutils.arg(
    '--backend',
    metavar='<backend>',
    type=str,
    default='.*',
    help='Filter results by backend name.  Regular expressions are supported.')
@cliutils.arg(
    '--pool',
    metavar='<pool>',
    type=str,
    default='.*',
    help='Filter results by pool name.  Regular expressions are supported.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "name,host"')
def do_pool_list(cs, args):
    """List all backend storage pools known to the scheduler (Admin only)."""

    search_opts = {
        'host': args.host,
        'backend': args.backend,
        'pool': args.pool,
    }
    fields = ["Name", "Host", "Backend", "Pool"]
    if args.columns is not None:
        fields = _split_columns(columns=args.columns)

    pools = cs.pools.list(detailed=False, search_opts=search_opts)
    cliutils.print_list(pools, fields=fields)


@cliutils.arg(
    'share_type',
    metavar='<share_type>',
    help="Filter results by share type name or ID.")
def do_type_access_list(cs, args):
    """Print access information about the given share type (Admin only)."""
    share_type = _find_share_type(cs, args.share_type)
    if share_type.is_public:
        raise exceptions.CommandError("Forbidden to get access list "
                                      "for public share type.")
    access_list = cs.share_type_access.list(share_type)

    columns = ['Project_ID']
    cliutils.print_list(access_list, columns)


@cliutils.arg(
    'share_type',
    metavar='<share_type>',
    help="Share type name or ID to add access"
         " for the given project.")
@cliutils.arg(
    'project_id',
    metavar='<project_id>',
    help='Project ID to add share type access for.')
def do_type_access_add(cs, args):
    """Adds share type access for the given project (Admin only)."""
    vtype = _find_share_type(cs, args.share_type)
    cs.share_type_access.add_project_access(vtype, args.project_id)


@cliutils.arg(
    'share_type',
    metavar='<share_type>',
    help=('Share type name or ID to remove access '
          'for the given project.'))
@cliutils.arg(
    'project_id',
    metavar='<project_id>',
    help='Project ID to remove share type access for.')
def do_type_access_remove(cs, args):
    """Removes share type access for the given project (Admin only)."""
    vtype = _find_share_type(cs, args.share_type)
    cs.share_type_access.remove_project_access(
        vtype, args.project_id)


@cliutils.arg('share', metavar='<share>',
              help='Name or ID of share to extend.')
@cliutils.arg('new_size',
              metavar='<new_size>',
              type=int,
              help='New size of share, in GiBs.')
def do_extend(cs, args):
    """Increases the size of an existing share."""
    share = _find_share(cs, args.share)
    cs.shares.extend(share, args.new_size)


@cliutils.arg('share', metavar='<share>',
              help='Name or ID of share to shrink.')
@cliutils.arg('new_size',
              metavar='<new_size>',
              type=int,
              help='New size of share, in GiBs.')
def do_shrink(cs, args):
    """Decreases the size of an existing share."""
    share = _find_share(cs, args.share)
    cs.shares.shrink(share, args.new_size)


@cliutils.arg(
    '--name',
    metavar='<name>',
    help='Optional consistency group name. (Default=None)',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional consistency group description. (Default=None)',
    default=None)
@cliutils.arg(
    '--share-types', '--share_types',
    metavar='<share_types>',
    type=str,
    default=None,
    action='single_alias',
    help='Optional list of share types. (Default=None)')
@cliutils.arg(
    '--share-network',
    '--share_network',
    metavar='<share_network>',
    type=str,
    default=None,
    action='single_alias',
    help='Specify share-network name or id.')
@cliutils.arg(
    '--source-cgsnapshot-id',
    '--source_cgsnapshot_id',
    metavar='<source_cgsnapshot_id>',
    type=str,
    action='single_alias',
    help='Optional snapshot ID to create the share from. (Default=None)',
    default=None)
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_create(cs, args):
    """Creates a new consistency group (Experimental)."""

    share_types = []
    if args.share_types:
        s_types = args.share_types.split(',')
        for s_type in s_types:
            share_type = _find_share_type(cs, s_type)
            share_types.append(share_type)

    share_network = None
    if args.share_network:
        share_network = _find_share_network(cs, args.share_network)

    kwargs = {'name': args.name, 'description': args.description}

    if share_types:
        kwargs['share_types'] = share_types
    if share_network:
        kwargs['share_network'] = share_network
    if args.source_cgsnapshot_id:
        kwargs['source_cgsnapshot_id'] = args.source_cgsnapshot_id

    consistency_group = cs.consistency_groups.create(**kwargs)

    _print_consistency_group(cs, consistency_group)


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of consistency groups to return. (Default=None)')
@cliutils.arg(
    '--offset',
    metavar="<offset>",
    default=None,
    help='Start position of consistency group listing.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_list(cs, args):
    """List consistency groups with filters (Experimental)."""
    list_of_keys = [
        'id', 'name', 'description', 'status',
    ]

    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)

    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    search_opts = {
        'all_tenants': all_tenants,
        'offset': args.offset,
        'limit': args.limit,
    }
    consistency_groups = cs.consistency_groups.list(
        search_opts=search_opts,
    )
    cliutils.print_list(consistency_groups, fields=list_of_keys)


@cliutils.arg(
    'consistency_group',
    metavar='<consistency_group>',
    help='Name or ID of the consistency group.')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_show(cs, args):
    """Show details about a consistency group (Experimental)."""
    consistency_group = _find_consistency_group(cs, args.consistency_group)
    _print_consistency_group(cs, consistency_group)


@cliutils.arg(
    'consistency_group',
    metavar='<consistency_group>',
    help='Name or ID of the consistency group to update.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Optional new name for the consistency group. (Default=None)')
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional consistency group description. (Default=None)',
    default=None)
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_update(cs, args):
    """Update a consistency group (Experimental)."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name
    if args.description is not None:
        kwargs['description'] = args.description

    if not kwargs:
        msg = "Must supply name and/or description"
        raise exceptions.CommandError(msg)
    _find_consistency_group(cs, args.consistency_group).update(**kwargs)


@cliutils.arg(
    'consistency_group',
    metavar='<consistency_group>',
    nargs='+',
    help='Name or ID of the consistency group(s).')
@cliutils.arg(
    '--force',
    action='store_true',
    default=False,
    help='Attempt to force delete the consistency group (Default=False)'
         ' (Admin only).')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_delete(cs, args):
    """Remove one or more consistency groups (Experimental)."""
    failure_count = 0
    kwargs = {}

    if args.force is not None:
        kwargs['force'] = args.force

    for consistency_group in args.consistency_group:
        try:
            cg_ref = _find_consistency_group(cs, consistency_group)
            cs.consistency_groups.delete(cg_ref, **kwargs)
        except Exception as e:
            failure_count += 1
            print("Delete for consistency group %s failed: %s" % (
                consistency_group, e), file=sys.stderr)

    if failure_count == len(args.consistency_group):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "consistency groups.")


@cliutils.arg(
    'consistency_group',
    metavar='<consistency_group>',
    help='Name or ID of the consistency group state to modify.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the consistency group. '
          'Options include available, error, creating, deleting, '
          'error_deleting. If no state is provided, '
          'available will be used.'))
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_reset_state(cs, args):
    """Explicitly update the state of a consistency group

    (Admin only, Experimental).
    """
    cg = _find_consistency_group(cs, args.consistency_group)
    cs.consistency_groups.reset_state(cg, args.state)


@cliutils.arg(
    'consistency_group',
    metavar='<consistency_group>',
    help='Name or ID of the consistency group.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    help='Optional consistency group snapshot name. (Default=None)',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional consistency group snapshot description. (Default=None)',
    default=None)
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_create(cs, args):
    """Creates a new consistency group snapshot (Experimental)."""

    kwargs = {'name': args.name, 'description': args.description}

    consistency_group = _find_consistency_group(cs, args.consistency_group)
    consistency_group_id = consistency_group.id
    cg_snapshot = cs.cg_snapshots.create(consistency_group_id, **kwargs)
    _print_consistency_group(cs, cg_snapshot)


def _split_columns(columns, title=True):
    if title:
        list_of_keys = list(map(lambda x: x.strip().title(),
                                columns.split(",")))
    else:
        list_of_keys = list(map(lambda x: x.strip().lower(),
                                columns.split(",")))
    return list_of_keys


@cliutils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of consistency group snapshots to return.'
         '(Default=None)')
@cliutils.arg(
    '--offset',
    metavar="<offset>",
    default=None,
    help='Start position of consistency group snapshot listing.')
@cliutils.arg(
    '--detailed',
    dest='detailed',
    default=True,
    help='Show detailed information about snapshots.')
@cliutils.arg(
    '--columns',
    metavar='<columns>',
    type=str,
    default=None,
    help='Comma separated list of columns to be displayed '
         'e.g. --columns "id,name"')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_list(cs, args):
    """List consistency group snapshots with filters (Experimental)."""
    list_of_keys = [
        'id', 'name', 'description', 'status',
    ]
    if args.columns is not None:
        list_of_keys = _split_columns(columns=args.columns)
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    search_opts = {
        'all_tenants': all_tenants,
        'offset': args.offset,
        'limit': args.limit,
    }
    cg_snapshot = cs.cg_snapshots.list(
        detailed=args.detailed,
        search_opts=search_opts,
    )
    cliutils.print_list(cg_snapshot, fields=list_of_keys)


@cliutils.arg(
    'cg_snapshot',
    metavar='<cg_snapshot>',
    help='Name or ID of the consistency group snapshot.')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_show(cs, args):
    """Show details about a consistency group snapshot (Experimental)."""
    cg_snapshot = _find_cg_snapshot(cs, args.cg_snapshot)
    _print_cg_snapshot(cs, cg_snapshot)


@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the consistency group. '
          'Options include available, error, creating, deleting, '
          'error_deleting. If no state is provided, '
          'available will be used.'))
@cliutils.arg(
    'cg_snapshot',
    metavar='<cg_snapshot>',
    help='Name or ID of the consistency group snapshot.')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_reset_state(cs, args):
    """Explicitly update the state of a consistency group

    (Admin only, Experimental).
    """
    cg = _find_cg_snapshot(cs, args.cg_snapshot)
    cs.cg_snapshots.reset_state(cg, args.state)


@cliutils.arg(
    '--limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of shares to return. (Default=None)')
@cliutils.arg(
    '--offset',
    metavar="<offset>",
    default=None,
    help='Start position of security services listing.')
@cliutils.arg(
    'cg_snapshot',
    metavar='<cg_snapshot>',
    help='Name or ID of the consistency group snapshot.')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_members(cs, args):
    """Get member details for a consistency group snapshot (Experimental)."""
    cg_snapshot = _find_cg_snapshot(cs, args.cg_snapshot)

    search_opts = {
        'offset': args.offset,
        'limit': args.limit,
    }

    cg_members = cs.cg_snapshots.members(
        cg_snapshot,
        search_opts
    )

    list_of_keys = [
        'Id',
        'Size',
        'Created_at',
        'Share_protocol',
        'Share_id',
        'Share_type_id',
    ]

    cliutils.print_list(cg_members, fields=list_of_keys)


@cliutils.arg(
    'cg_snapshot',
    metavar='<cg_snapshot>',
    help='Name or ID of the cg snapshot to update.')
@cliutils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Optional new name for the cg snapshot. (Default=None')
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional cg snapshot description. (Default=None)',
    default=None)
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_update(cs, args):
    """Update a consistency group snapshot (Experimental)."""
    kwargs = {}

    if args.name is not None:
        kwargs['name'] = args.name
    if args.description is not None:
        kwargs['description'] = args.description

    if not kwargs:
        msg = "Must supply name and/or description"
        raise exceptions.CommandError(msg)
    _find_cg_snapshot(cs, args.cg_snapshot).update(**kwargs)


@cliutils.arg(
    'cg_snapshot',
    metavar='<cg_snapshot>',
    nargs='+',
    help='Name or ID of the consistency group snapshot.')
@cliutils.arg(
    '--force',
    action='store_true',
    default=False,
    help='Attempt to force delete the cg snapshot(s) (Default=False)'
         ' (Admin only).')
@cliutils.service_type('sharev2')
@api_versions.experimental_api
def do_cg_snapshot_delete(cs, args):
    """Remove one or more consistency group snapshots (Experimental)."""
    failure_count = 0
    kwargs = {}

    if args.force is not None:
        kwargs['force'] = args.force

    for cg_snapshot in args.cg_snapshot:
        try:
            cg_ref = _find_cg_snapshot(cs, cg_snapshot)

            cs.cg_snapshots.delete(cg_ref, **kwargs)
        except Exception as e:
            failure_count += 1
            print("Delete for consistency group snapshot %s failed: %s" % (
                cg_snapshot, e), file=sys.stderr)

    if failure_count == len(args.cg_snapshot):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "consistency group snapshots.")


@cliutils.arg(
    '--share-id',
    '--share_id',
    '--si',  # alias
    metavar='<share_id>',
    default=None,
    action='single_alias',
    help='List replicas belonging to share.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_list(cs, args):
    """List share replicas (Experimental)."""
    share = _find_share(cs, args.share_id) if args.share_id else None

    list_of_keys = [
        'ID',
        'Status',
        'Replica State',
        'Share ID',
        'Host',
        'Availability Zone',
        'Updated At',
    ]
    if share:
        replicas = cs.share_replicas.list(share)
    else:
        replicas = cs.share_replicas.list()

    cliutils.print_list(replicas, list_of_keys)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to replicate.')
@cliutils.arg(
    '--availability-zone',
    '--availability_zone',
    '--az',
    default=None,
    action='single_alias',
    metavar='<availability-zone>',
    help='Optional Availability zone in which replica should be created.')
@cliutils.arg(
    '--share-network',
    '--share_network',
    metavar='<network-info>',
    default=None,
    action='single_alias',
    help='Optional network info ID or name.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_create(cs, args):
    """Create a share replica (Experimental)."""
    share = _find_share(cs, args.share)

    share_network = None
    if args.share_network:
        share_network = _find_share_network(cs, args.share_network)

    replica = cs.share_replicas.create(share,
                                       args.availability_zone,
                                       share_network)
    _print_share_replica(cs, replica)


@cliutils.arg(
    'replica',
    metavar='<replica>',
    help='ID of the share replica.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_show(cs, args):
    """Show details about a replica (Experimental)."""

    replica = cs.share_replicas.get(args.replica)
    _print_share_replica(cs, replica)


@cliutils.arg(
    'replica',
    metavar='<replica>',
    nargs='+',
    help='ID of the share replica.')
@cliutils.arg(
    '--force',
    action='store_true',
    default=False,
    help='Attempt to force deletion of a replica on its backend. Using '
         'this option will purge the replica from Manila even if it '
         'is not cleaned up on the backend. Defaults to False.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_delete(cs, args):
    """Remove one or more share replicas (Experimental)."""
    failure_count = 0
    kwargs = {}

    if args.force is not None:
        kwargs['force'] = args.force

    for replica in args.replica:
        try:
            replica_ref = _find_share_replica(cs, replica)
            cs.share_replicas.delete(replica_ref, **kwargs)
        except Exception as e:
            failure_count += 1
            print("Delete for share replica %s failed: %s" % (replica, e),
                  file=sys.stderr)

    if failure_count == len(args.replica):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "replicas.")


@cliutils.arg(
    'replica',
    metavar='<replica>',
    help='ID of the share replica.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_promote(cs, args):
    """Promote specified replica to 'active' replica_state (Experimental)."""
    replica = _find_share_replica(cs, args.replica)
    cs.share_replicas.promote(replica)


@cliutils.arg(
    'replica',
    metavar='<replica>',
    help='ID of the share replica to modify.')
@cliutils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the replica. Options include '
          'available, error, creating, deleting, error_deleting. If no '
          'state is provided, available will be used.'))
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_reset_state(cs, args):
    """Explicitly update the 'status' of a share replica (Experimental)."""
    replica = _find_share_replica(cs, args.replica)
    cs.share_replicas.reset_state(replica, args.state)


@cliutils.arg(
    'replica',
    metavar='<replica>',
    help='ID of the share replica to modify.')
@cliutils.arg(
    '--replica-state',
    '--replica_state',
    '--state',  # alias for user sanity
    metavar='<replica_state>',
    default='out_of_sync',
    action='single_alias',
    help=('Indicate which replica_state to assign the replica. Options '
          'include in_sync, out_of_sync, active, error. If no '
          'state is provided, out_of_sync will be used.'))
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_reset_replica_state(cs, args):
    """Explicitly update the 'replica_state' of a share replica

    (Experimental).
    """
    replica = _find_share_replica(cs, args.replica)
    cs.share_replicas.reset_replica_state(replica, args.replica_state)


@cliutils.arg(
    'replica',
    metavar='<replica>',
    help='ID of the share replica to resync.')
@api_versions.wraps("2.11")
@api_versions.experimental_api
def do_share_replica_resync(cs, args):
    """Attempt to update the share replica with its 'active' mirror

     (Experimental).
     """
    replica = _find_share_replica(cs, args.replica)
    cs.share_replicas.resync(replica)
