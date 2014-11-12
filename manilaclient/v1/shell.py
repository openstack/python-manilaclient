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

from manilaclient.common import constants
from manilaclient import exceptions
from manilaclient.openstack.common.apiclient import utils as apiclient_utils
from manilaclient.openstack.common import cliutils
from manilaclient import utils
from manilaclient.v1 import quotas


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


def _print_share(cs, share):
    info = share._info.copy()
    utils.print_dict(info)


def _find_share_snapshot(cs, snapshot):
    """Get a snapshot by ID."""
    return apiclient_utils.find_resource(cs.share_snapshots, snapshot)


def _print_share_snapshot(cs, snapshot):
    info = snapshot._info.copy()
    info.pop('links')
    utils.print_dict(info)


def _find_share_network(cs, share_network):
    "Get a share network by ID or name."
    return apiclient_utils.find_resource(cs.share_networks, share_network)


def _find_security_service(cs, security_service):
    "Get a security service by ID or name."
    return apiclient_utils.find_resource(cs.security_services,
                                         security_service)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _extract_metadata(args):
    metadata = {}
    if args.metadata:
        for metadatum in args.metadata:
            # unset doesn't require a val, so we have the if/else
            if '=' in metadatum:
                (key, value) = metadatum.split('=', 1)
            else:
                key = metadatum
                value = None

            metadata[key] = value
    return metadata


def _extract_extra_specs(args):
    extra_specs = {}
    if args.extra_specs:
        for extra_spec in args.extra_specs:
            # unset doesn't require a val, so we have the if/else
            if '=' in extra_spec:
                (key, value) = extra_spec.split('=', 1)
            else:
                key = extra_spec
                value = None

            extra_specs[key] = value
    return extra_specs


def do_endpoints(cs, args):
    """Discover endpoints that get returned from the authenticate services."""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['access']['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


def do_credentials(cs, args):
    """Show user credentials returned from auth."""
    catalog = cs.client.service_catalog.catalog
    utils.print_dict(catalog['access']['user'], "User Credentials")
    utils.print_dict(catalog['access']['token'], "Token")

_quota_resources = ['shares', 'snapshots', 'gigabytes', 'share_networks']


def _quota_show(quotas):
    quota_dict = {}
    for resource in _quota_resources:
        quota_dict[resource] = getattr(quotas, resource, None)
    utils.print_dict(quota_dict)


def _quota_update(manager, identifier, args):
    updates = {}
    for resource in _quota_resources:
        val = getattr(args, resource, None)
        if val is not None:
            updates[resource] = val

    if updates:
        # default value of force is None to make sure this client
        # will be compatibile with old nova server
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

    if not args.tenant:
        _quota_show(cs.quotas.get(cs.client.tenant_id, user_id=args.user))
    else:
        _quota_show(cs.quotas.get(args.tenant, user_id=args.user))


@cliutils.arg(
    '--tenant',
    metavar='<tenant-id>',
    default=None,
    help='ID of tenant to list the default quotas for.')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    if not args.tenant:
        _quota_show(cs.quotas.defaults(cs.client.tenant_id))
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
    '--share-networks',
    metavar='<share-networks>',
    type=int,
    default=None,
    help='New value for the "share_networks" quota.')
@cliutils.arg(
    '--force',
    dest='force',
    action="store_true",
    default=None,
    help='Whether force update the quota even if the already used '
         'and reserved exceeds the new quota.')
@cliutils.service_type('share')
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user."""

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

    The quota will revert back to default.
    """

    if not args.tenant:
        cs.quotas.delete(cs.client.tenant_id, user_id=args.user)
    else:
        cs.quotas.delete(args.tenant, user_id=args.user)


@cliutils.arg(
    'class_name',
    metavar='<class>',
    help='Name of quota class to list the quotas for.')
@cliutils.service_type('share')
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@cliutils.arg(
    'class-name',
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
    '--share-networks',
    metavar='<share-networks>',
    type=int,
    default=None,
    help='New value for the "share_networks" quota.')
@cliutils.service_type('share')
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@cliutils.service_type('share')
def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user."""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    utils.print_list(limits, columns)


@cliutils.service_type('share')
def do_rate_limits(cs, args):
    """Print a list of rate limits for a user."""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


@cliutils.arg(
    'share_protocol',
    metavar='<share_protocol>',
    type=str,
    help='Share type (NFS, CIFS or GlusterFS).')
@cliutils.arg(
    'size',
    metavar='<size>',
    type=int,
    help='Share size in GB.')
@cliutils.arg(
    '--snapshot-id',
    metavar='<snapshot-id>',
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
    metavar='<network-info>',
    help='Optional network info ID or name.',
    default=None)
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@cliutils.arg(
    '--volume-type',
    metavar='<volume-type>',
    help='Optional volume type. (Default=None)',
    default=None)
@cliutils.service_type('share')
def do_create(cs, args):
    """Creates new NAS storage (NFS, CIFS or GlusterFS)."""

    share_metadata = None
    if args.metadata is not None:
        share_metadata = _extract_metadata(args)

    share_network = None
    if args.share_network:
        share_network = _find_share_network(cs, args.share_network)
    share = cs.shares.create(args.share_protocol, args.size, args.snapshot_id,
                             args.name, args.description,
                             metadata=share_metadata,
                             share_network=share_network,
                             volume_type=args.volume_type)
    _print_share(cs, share)


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
@cliutils.service_type('share')
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
@cliutils.service_type('share')
def do_metadata_show(cs, args):
    """Show metadata of given share."""
    share = _find_share(cs, args.share)
    metadata = cs.shares.get_metadata(share)._info
    utils.print_dict(metadata, 'Metadata-property')


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
@cliutils.service_type('share')
def do_metadata_update_all(cs, args):
    """Update all metadata of a share."""
    share = _find_share(cs, args.share)
    metadata = _extract_metadata(args)
    metadata = share.update_all_metadata(metadata)._info['metadata']
    utils.print_dict(metadata, 'Metadata-property')


@cliutils.arg(
    'share',
    metavar='<share>',
    nargs='+',
    help='Name or ID of the share(s).')
def do_delete(cs, args):
    """Remove one or more shares."""
    failure_count = 0

    for share in args.share:
        try:
            share_ref = _find_share(cs, share)
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
    """Attempt force-delete of share, regardless of state."""
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


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share.')
@cliutils.service_type('share')
def do_show(cs, args):
    """Show details about a NAS share."""
    share = _find_share(cs, args.share)
    _print_share(cs, share)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@cliutils.arg(
    'access_type',
    metavar='<access_type>',
    help='Access rule type (only "ip", "user"(user or group), and "cert" '
         'are supported).')
@cliutils.arg(
    'access_to',
    metavar='<access_to>',
    help='Value that defines access.')
@cliutils.service_type('share')
def do_access_allow(cs, args):
    """Allow access to the share."""
    share = _find_share(cs, args.share)
    access = share.allow(args.access_type, args.access_to)
    utils.print_dict(access)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@cliutils.arg(
    'id',
    metavar='<id>',
    help='ID of the access rule to be deleted.')
@cliutils.service_type('share')
def do_access_deny(cs, args):
    """Deny access to a share."""
    share = _find_share(cs, args.share)
    share.deny(args.id)


@cliutils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
@cliutils.service_type('share')
def do_access_list(cs, args):
    """Show access list for share."""
    share = _find_share(cs, args.share)
    access_list = share.access_list()
    utils.print_list(access_list, ['id', 'access type', 'access to', 'state'])


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
    help='Filter results by share server ID.')
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
    help='Filters results by a extra specs key and value of volume type that '
         'was used for share creation. OPTIONAL: Default=None',
    default=None)
@cliutils.arg(
    '--volume-type',
    '--volume_type', '--volume-type-id',  # aliases
    '--volume-type_id', '--volume_type-id', '--volume_type_id',  # aliases
    metavar='<volume_type>',
    type=str,
    default=None,
    action='single_alias',
    help='Filter results by a volume type id or name that was used for share '
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
@cliutils.service_type('share')
def do_list(cs, args):
    """List NAS shares with filters."""
    list_of_keys = [
        'ID', 'Name', 'Size', 'Share Proto', 'Status', 'Volume Type',
        'Export location', 'Host',
    ]
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    empty_obj = type('Empty', (object,), {'id': None})
    volume_type = (_find_volume_type(cs, args.volume_type)
                   if args.volume_type else empty_obj)

    snapshot = (_find_share_snapshot(cs, args.snapshot)
                if args.snapshot else empty_obj)

    share_network = (_find_share_network(cs, args.share_network)
                     if args.share_network else empty_obj)
    search_opts = {
        'offset': args.offset,
        'limit': args.limit,
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'host': args.host,
        'share_network_id': share_network.id,
        'snapshot_id': snapshot.id,
        'volume_type_id': volume_type.id,
        'metadata': _extract_metadata(args),
        'extra_specs': _extract_extra_specs(args),
        'share_server_id': args.share_server_id,
        'project_id': args.project_id,
    }
    shares = cs.shares.list(
        search_opts=search_opts,
        sort_key=args.sort_key,
        sort_dir=args.sort_dir,
    )
    utils.print_list(shares, list_of_keys)


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
    default='any',
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
         'OPTIONAL: Default=None.' % {
             'keys': constants.SNAPSHOT_SORT_KEY_VALUES})
@cliutils.arg(
    '--sort-dir',
    '--sort_dir',  # alias
    metavar='<sort_dir>',
    type=str,
    default=None,
    action='single_alias',
    help='Sort direction, available values are %(values)s. '
         'OPTIONAL: Default=None.' % {'values': constants.SORT_DIR_VALUES})
@cliutils.service_type('share')
def do_snapshot_list(cs, args):
    """List all the snapshots."""
    list_of_keys = [
        'ID', 'Share ID', 'Status', 'Name', 'Share Size',
    ]
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
    utils.print_list(snapshots, list_of_keys)


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot.')
@cliutils.service_type('share')
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
@cliutils.service_type('share')
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
    'name',
    nargs='?',
    metavar='<name>',
    help='New name for the share.')
@cliutils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@cliutils.service_type('share')
def do_rename(cs, args):
    """Rename a share."""
    kwargs = {}

    if args.name is not None:
        kwargs['display_name'] = args.name
    if args.description is not None:
        kwargs['display_description'] = args.description
    if not kwargs:
        msg = "Must supply either name or description."
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
@cliutils.service_type('share')
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
@cliutils.service_type('share')
def do_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.delete()


@cliutils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to force delete.')
@cliutils.service_type('share')
def do_snapshot_force_delete(cs, args):
    """Attempt force-delete of snapshot, regardless of state."""
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
@cliutils.service_type('share')
def do_snapshot_reset_state(cs, args):
    """Explicitly update the state of a snapshot."""
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
@cliutils.service_type('share')
def do_reset_state(cs, args):
    """Explicitly update the state of a share."""
    share = _find_share(cs, args.share)
    share.reset_state(args.state)


@cliutils.arg(
    '--neutron-net-id',
    metavar='neutron-net-id',
    default=None,
    help="Neutron network ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-subnet-id',
    metavar='neutron-subnet-id',
    default=None,
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
    values = {'neutron_net_id': args.neutron_net_id,
              'neutron_subnet_id': args.neutron_subnet_id,
              'name': args.name,
              'description': args.description}
    share_network = cs.share_networks.create(**values)
    info = share_network._info.copy()
    utils.print_dict(info)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of share network to update.')
@cliutils.arg(
    '--neutron-net-id',
    metavar='neutron-net-id',
    default=None,
    help="Neutron network ID. Used to set up network for share servers.")
@cliutils.arg(
    '--neutron-subnet-id',
    metavar='neutron-subnet-id',
    default=None,
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
    values = {'neutron_net_id': args.neutron_net_id,
              'neutron_subnet_id': args.neutron_subnet_id,
              'name': args.name,
              'description': args.description}
    share_network = _find_share_network(
        cs, args.share_network).update(**values)
    info = share_network._info.copy()
    utils.print_dict(info)


@cliutils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of the share network to show.')
def do_share_network_show(cs, args):
    """Get a description for network used by the tenant."""
    share_network = _find_share_network(cs, args.share_network)
    info = share_network._info.copy()
    utils.print_dict(info)


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
def do_share_network_list(cs, args):
    """Get a list of network info."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'project_id': args.project_id,
        'name': args.name,
        'created_since': args.created_since,
        'created_before': args.created_before,
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
    utils.print_list(share_networks, fields=fields)


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
def do_share_network_security_service_list(cs, args):
    """Get list of security services associated with a given share network."""
    share_network = _find_share_network(cs, args.share_network)
    search_opts = {
        'share_network_id': share_network.id,
    }
    security_services = cs.security_services.list(search_opts=search_opts)
    fields = ['id', 'name', 'status', 'type', ]
    utils.print_list(security_services, fields=fields)


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
    utils.print_dict(info)


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
    utils.print_dict(security_service._info)


@cliutils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service name or ID to show.')
def do_security_service_show(cs, args):
    """Show security service."""
    security_service = _find_security_service(cs, args.security_service)
    info = security_service._info.copy()
    utils.print_dict(info)


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
    if args.detailed:
        fields.append('share_networks')
    utils.print_list(security_services, fields=fields)


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
def do_share_server_list(cs, args):
    """List all share servers."""
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
    share_servers = cs.share_servers.list(search_opts=search_opts)
    utils.print_list(share_servers, fields=fields)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_show(cs, args):
    """Show share server info."""
    share_server = cs.share_servers.get(args.id)
    # All 'backend_details' data already present as separated strings,
    # so remove big dict from view.
    if "backend_details" in share_server._info:
        del share_server._info["backend_details"]
    utils.print_dict(share_server._info)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_details(cs, args):
    """Show share server details."""
    details = cs.share_servers.details(args.id)
    utils.print_dict(details._info)


@cliutils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='ID of share server.')
def do_share_server_delete(cs, args):
    """Delete share server."""
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
def do_service_list(cs, args):
    """List all services."""
    search_opts = {
        'status': args.status,
        'host': args.host,
        'binary': args.binary,
        'zone': args.zone,
        'state': args.state,
    }
    fields = ["Binary", "Host", "Zone", "Status", "State", "Updated_at"]
    services = cs.services.list(search_opts=search_opts)
    utils.print_list(services, fields=fields)


def _print_type_extra_specs(vol_type):
    try:
        return vol_type.get_keys()
    except exceptions.NotFound:
        return "N/A"


def _print_volume_type_list(vtypes):
    utils.print_list(vtypes, ['ID', 'Name'])


def _print_type_and_extra_specs_list(vtypes):
    formatters = {'extra_specs': _print_type_extra_specs}
    utils.print_list(vtypes, ['ID', 'Name', 'extra_specs'], formatters)


def _find_volume_type(cs, vtype):
    """Get a volume type by name or ID."""
    return apiclient_utils.find_resource(cs.volume_types, vtype)


@cliutils.service_type('share')
def do_type_list(cs, args):
    """Print a list of available 'volume types'."""
    vtypes = cs.volume_types.list()
    _print_volume_type_list(vtypes)


@cliutils.service_type('share')
def do_extra_specs_list(cs, args):
    """Print a list of current 'volume types and extra specs' (Admin Only)."""
    vtypes = cs.volume_types.list()
    _print_type_and_extra_specs_list(vtypes)


@cliutils.arg(
    'name',
    metavar='<name>',
    help="Name of the new volume type.")
@cliutils.service_type('share')
def do_type_create(cs, args):
    """Create a new volume type."""
    vtype = cs.volume_types.create(args.name)
    _print_volume_type_list([vtype])


@cliutils.arg(
    'id',
    metavar='<id>',
    help="Name or ID of the volume type to delete.")
@cliutils.service_type('share')
def do_type_delete(cs, args):
    """Delete a specific volume type."""
    volume_type = _find_volume_type(cs, args.id)
    cs.volume_types.delete(volume_type)


@cliutils.arg(
    'vtype',
    metavar='<vtype>',
    help="Name or ID of the volume type.")
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
@cliutils.service_type('share')
def do_type_key(cs, args):
    """Set or unset extra_spec for a volume type."""
    vtype = _find_volume_type(cs, args.vtype)

    if args.metadata is not None:
        keypair = _extract_metadata(args)

        if args.action == 'set':
            vtype.set_keys(keypair)
        elif args.action == 'unset':
            vtype.unset_keys(list(keypair))
