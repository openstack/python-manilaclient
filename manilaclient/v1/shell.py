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

import argparse
import os
import sys
import time

from manilaclient import exceptions
from manilaclient import utils


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

    print
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print "\nFinished"
            break
        elif status == "error":
            print "\nError %(action)s instance" % locals()
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _find_share(cs, share):
    """Get a share by ID."""
    return utils.find_resource(cs.shares, share)


def _print_share(cs, share):
    info = share._info.copy()
    utils.print_dict(info)


def _find_share_snapshot(cs, snapshot):
    """Get a snapshot by ID."""
    return utils.find_resource(cs.share_snapshots, snapshot)


def _print_share_snapshot(cs, snapshot):
    info = snapshot._info.copy()
    info.pop('links')
    utils.print_dict(info)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata[0]:
        # unset doesn't require a val, so we have the if/else
        if '=' in metadatum:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata


def do_endpoints(cs, args):
    """Discover endpoints that get returned from the authenticate services"""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['access']['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


def do_credentials(cs, args):
    """Show user credentials returned from auth"""
    catalog = cs.client.service_catalog.catalog
    utils.print_dict(catalog['access']['user'], "User Credentials")
    utils.print_dict(catalog['access']['token'], "Token")

_quota_resources = ['shares', 'snapshots', 'gigabytes']


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
        manager.update(identifier, **updates)


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='UUID of tenant to list the quotas for.')
@utils.service_type('share')
def do_quota_show(cs, args):
    """List the quotas for a tenant."""

    _quota_show(cs.quotas.get(args.tenant))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='UUID of tenant to list the default quotas for.')
@utils.service_type('share')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    _quota_show(cs.quotas.defaults(args.tenant))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='UUID of tenant to set the quotas for.')
@utils.arg('--shares',
           metavar='<shares>',
           type=int, default=None,
           help='New value for the "shares" quota.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='New value for the "snapshots" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.service_type('share')
def do_quota_update(cs, args):
    """Update the quotas for a tenant."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg('class_name',
           metavar='<class>',
           help='Name of quota class to list the quotas for.')
@utils.service_type('share')
def do_quota_class_show(cs, args):
    """List the quotas for a quota class."""

    _quota_show(cs.quota_classes.get(args.class_name))


@utils.arg('class-name',
           metavar='<class-name>',
           help='Name of quota class to set the quotas for.')
@utils.arg('--shares',
           metavar='<shares>',
           type=int, default=None,
           help='New value for the "shares" quota.')
@utils.arg('--snapshots',
           metavar='<snapshots>',
           type=int, default=None,
           help='New value for the "snapshots" quota.')
@utils.arg('--gigabytes',
           metavar='<gigabytes>',
           type=int, default=None,
           help='New value for the "gigabytes" quota.')
@utils.service_type('share')
def do_quota_class_update(cs, args):
    """Update the quotas for a quota class."""

    _quota_update(cs.quota_classes, args.class_name, args)


@utils.service_type('share')
def do_absolute_limits(cs, args):
    """Print a list of absolute limits for a user"""
    limits = cs.limits.get().absolute
    columns = ['Name', 'Value']
    utils.print_list(limits, columns)


@utils.service_type('share')
def do_rate_limits(cs, args):
    """Print a list of rate limits for a user"""
    limits = cs.limits.get().rate
    columns = ['Verb', 'URI', 'Value', 'Remain', 'Unit', 'Next_Available']
    utils.print_list(limits, columns)


@utils.arg(
    'share_protocol',
    metavar='<share_protocol>',
    type=str,
    help='Share type (NFS or CIFS)')
@utils.arg(
    'size',
    metavar='<size>',
    type=int,
    help='Share size in GB')
@utils.arg(
    '--snapshot-id',
    metavar='<snapshot-id>',
    help='Optional snapshot id to create the share from. (Default=None)',
    default=None)
@utils.arg(
    '--name',
    metavar='<name>',
    help='Optional share name. (Default=None)',
    default=None)
@utils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@utils.service_type('share')
def do_create(cs, args):
    """Creates new NAS storage (NFS or CIFS)."""
    share = cs.shares.create(args.share_protocol, args.size, args.snapshot_id,
                             args.name, args.description)
    _print_share(cs, share)


@utils.arg(
    'share',
    metavar='<share>',
    help='ID of the NAS to delete.')
@utils.service_type('share')
def do_delete(cs, args):
    """Deletes NAS storage."""
    cs.shares.delete(args.share)


@utils.arg(
    'share',
    metavar='<share>',
    help='ID of the NAS share.')
@utils.service_type('share')
def do_show(cs, args):
    """Show details about a NAS share."""
    share = _find_share(cs, args.share)
    _print_share(cs, share)


@utils.arg(
    'share',
    metavar='<share>',
    help='ID of the NAS share to modify.')
@utils.arg(
    'access_type',
    metavar='<access_type>',
    help='access rule type (only "ip" is supported).')
@utils.arg(
    'access_to',
    metavar='<access_to>',
    help='Value that defines access')
@utils.service_type('share')
def do_allow_access(cs, args):
    """Allow access to the share."""
    share = _find_share(cs, args.share)
    share.allow(args.access_type, args.access_to)


@utils.arg(
    'share',
    metavar='<share>',
    help='ID of the NAS share to modify.')
@utils.arg(
    'id',
    metavar='<id>',
    help='id of the access rule to be deleted.')
@utils.service_type('share')
def do_deny_access(cs, args):
    """Deny access to a share."""
    share = _find_share(cs, args.share)
    share.deny(args.id)


@utils.arg(
    'share',
    metavar='<share>',
    help='ID of the share.')
@utils.service_type('share')
def do_access_list(cs, args):
    """Show access list for share."""
    share = _find_share(cs, args.share)
    access_list = share.access_list()
    utils.print_list(access_list, ['id', 'access type', 'access to', 'state'])


@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Filter results by name')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
@utils.service_type('share')
def do_list(cs, args):
    """List all NAS shares."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
    }
    shares = cs.shares.list(search_opts=search_opts)
    utils.print_list(shares,
                     ['ID', 'Name', 'Size', 'Share Proto', 'Status',
                      'Export location'])


@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Display information from all tenants (Admin only).')
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Filter results by name')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
@utils.arg(
    '--share-id',
    metavar='<share-id>',
    default=None,
    help='Filter results by share-id')
@utils.service_type('share')
def do_snapshot_list(cs, args):
    """List all the snapshots."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'name': args.name,
        'status': args.status,
        'share_id': args.share_id,
    }
    snapshots = cs.share_snapshots.list(search_opts=search_opts)
    utils.print_list(snapshots,
                     ['ID', 'Share ID', 'Status', 'Name', 'Share Size'])


@utils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='ID of the snapshot.')
@utils.service_type('share')
def do_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    _print_share_snapshot(cs, snapshot)


@utils.arg(
    'share_id',
    metavar='<share-id>',
    help='ID of the share to snapshot')
@utils.arg(
    '--force',
    metavar='<True|False>',
    help='Optional flag to indicate whether '
    'to snapshot a share even if it\'s busy.'
    ' (Default=False)',
    default=False)
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help='Optional snapshot name. (Default=None)')
@utils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help='Optional snapshot description. (Default=None)')
@utils.service_type('share')
def do_snapshot_create(cs, args):
    """Add a new snapshot."""
    snapshot = cs.share_snapshots.create(args.share_id,
                                         args.force,
                                         args.name,
                                         args.description)
    _print_share_snapshot(cs, snapshot)

# @utils.arg('share',
#            metavar='<share>',
#            help='ID of the share to rename.')
# @utils.arg('name',
#            nargs='?',
#            metavar='<name>',
#            help='New name for the share.')
# @utils.arg('--description', metavar='<description>',
#            help='Optional share description. (Default=None)',
#            default=None)
# @utils.arg('--display-description',
#            help=argparse.SUPPRESS)
# @utils.arg('--display_description',
#            help=argparse.SUPPRESS)
# @utils.service_type('share')
# def do_rename(cs, args):
#     """Rename a share."""
#     kwargs = {}
#
#     if args.name is not None:
#         kwargs['name'] = args.name
#     if args.display_description is not None:
#         kwargs['description'] = args.display_description
#     elif args.description is not None:
#         kwargs['description'] = args.description
#
#     _find_share(cs, args.share).update(**kwargs)


@utils.arg(
    'snapshot_id',
    metavar='<snapshot-id>',
    help='ID of the snapshot to delete.')
@utils.service_type('share')
def do_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot_id)
    snapshot.delete()
