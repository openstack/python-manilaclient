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

import os
import sys
import time

from manilaclient import exceptions
from manilaclient.v1 import quotas
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


def _find_share_network(cs, share_network):
    "Get a share network by ID or name."
    return utils.find_resource(cs.share_networks, share_network)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata:
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


@utils.arg('--tenant',
           metavar='<tenant-id>',
           default=None,
           help='ID of tenant to list the quotas for.')
@utils.arg('--user',
           metavar='<user-id>',
           default=None,
           help='ID of user to list the quotas for.')
def do_quota_show(cs, args):
    """List the quotas for a tenant/user."""

    if not args.tenant:
        _quota_show(cs.quotas.get(cs.client.tenant_id, user_id=args.user))
    else:
        _quota_show(cs.quotas.get(args.tenant, user_id=args.user))


@utils.arg('--tenant',
           metavar='<tenant-id>',
           default=None,
           help='ID of tenant to list the default quotas for.')
def do_quota_defaults(cs, args):
    """List the default quotas for a tenant."""

    if not args.tenant:
        _quota_show(cs.quotas.defaults(cs.client.tenant_id))
    else:
        _quota_show(cs.quotas.defaults(args.tenant))


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='UUID of tenant to set the quotas for.')
@utils.arg('--user',
           metavar='<user-id>',
           default=None,
           help='ID of user to set the quotas for.')
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
@utils.arg('--share-networks',
           metavar='<share-networks>',
           type=int, default=None,
           help='New value for the "share_networks" quota.')
@utils.arg('--force',
           dest='force',
           action="store_true",
           default=None,
           help='Whether force update the quota even if the already used'
                ' and reserved exceeds the new quota')
@utils.service_type('share')
def do_quota_update(cs, args):
    """Update the quotas for a tenant/user."""

    _quota_update(cs.quotas, args.tenant, args)


@utils.arg('--tenant',
           metavar='<tenant-id>',
           help='ID of tenant to delete quota for.')
@utils.arg('--user',
           metavar='<user-id>',
           help='ID of user to delete quota for.')
def do_quota_delete(cs, args):
    """Delete quota for a tenant/user so their quota will Revert
       back to default.
    """

    if not args.tenant:
        cs.quotas.delete(cs.client.tenant_id, user_id=args.user)
    else:
        cs.quotas.delete(args.tenant, user_id=args.user)


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
@utils.arg('--share-networks',
           metavar='<share-networks>',
           type=int, default=None,
           help='New value for the "share_networks" quota.')
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
@utils.arg('--metadata',
           type=str,
           nargs='*',
           metavar='<key=value>',
           help='Metadata key=value pairs (Optional, Default=None)',
           default=None)
@utils.arg(
    '--share-network',
    metavar='<network-info>',
    help='Optional network info id or name',
    default=None)
@utils.arg(
    '--description',
    metavar='<description>',
    help='Optional share description. (Default=None)',
    default=None)
@utils.arg(
    '--volume-type',
    metavar='<volume-type>',
    help='Optional volume type. (Default=None)',
    default=None)
@utils.service_type('share')
def do_create(cs, args):
    """Creates new NAS storage (NFS or CIFS)."""

    share_metadata = None
    if args.metadata is not None:
        share_metadata = _extract_metadata(args)

    share_network = _find_share_network(cs, args.share_network)
    share = cs.shares.create(args.share_protocol, args.size, args.snapshot_id,
                             args.name, args.description,
                             metadata=share_metadata,
                             share_network=share_network,
                             volume_type=args.volume_type)
    _print_share(cs, share)


@utils.arg('share',
           metavar='<share>',
           help='Name or ID of the share to update metadata on.')
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="Actions: 'set' or 'unset'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata to set/unset (only key is necessary on unset)')
@utils.service_type('share')
def do_metadata(cs, args):
    """Set or Delete metadata on a share."""
    share = utils.find_share(cs, args.share)
    metadata = _extract_metadata(args)

    if args.action == 'set':
        cs.shares.set_metadata(share, metadata)
    elif args.action == 'unset':
        cs.shares.delete_metadata(share, sorted(metadata.keys(),
                                  reverse=True))


@utils.arg('share', metavar='<share>',
           help='Name or ID of share')
@utils.service_type('share')
def do_metadata_show(cs, args):
    """Show metadata of given share."""
    share = utils.find_share(cs, args.share)
    metadata = cs.shares.get_metadata(share)._info
    utils.print_dict(metadata, 'Metadata-property')


@utils.arg('share',
           metavar='<share>',
           help='Name or ID of the share to update metadata on.')
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='+',
           default=[],
           help='Metadata entry/entries to update.')
@utils.service_type('share')
def do_metadata_update_all(cs, args):
    """Update all metadata of a share."""
    share = utils.find_share(cs, args.share)
    metadata = _extract_metadata(args)
    metadata = share.update_all_metadata(metadata)._info['metadata']
    utils.print_dict(metadata, 'Metadata-property')


@utils.arg('share', metavar='<share>', nargs='+',
           help='Name or ID of share(s).')
def do_delete(cs, args):
    """Removes one or more shares."""
    failure_count = 0

    for share in args.share:
        try:
            share_ref = _find_share(cs, share)
            share_ref.delete()
        except Exception as e:
            failure_count += 1
            if 'Access was denied' in e.message:
                print('Error occurred while deleting share %s' % share_ref.id)
            else:
                print(e.message)

    if failure_count == len(args.share):
        raise exceptions.CommandError("Unable to delete any of the specified "
                                      "shares.")


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share.')
@utils.service_type('share')
def do_show(cs, args):
    """Show details about a NAS share."""
    share = _find_share(cs, args.share)
    _print_share(cs, share)


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@utils.arg(
    'access_type',
    metavar='<access_type>',
    help='access rule type (only "ip" and "sid"(user or group) '
         'are supported).')
@utils.arg(
    'access_to',
    metavar='<access_to>',
    help='Value that defines access')
@utils.service_type('share')
def do_access_allow(cs, args):
    """Allow access to the share."""
    share = _find_share(cs, args.share)
    access = share.allow(args.access_type, args.access_to)
    utils.print_dict(access)


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the NAS share to modify.')
@utils.arg(
    'id',
    metavar='<id>',
    help='id of the access rule to be deleted.')
@utils.service_type('share')
def do_access_deny(cs, args):
    """Deny access to a share."""
    share = _find_share(cs, args.share)
    share.deny(args.id)


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share.')
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
    help='Name or ID of the snapshot.')
@utils.service_type('share')
def do_snapshot_show(cs, args):
    """Show details about a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    _print_share_snapshot(cs, snapshot)


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to snapshot')
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
    share = utils.find_share(cs, args.share)
    snapshot = cs.share_snapshots.create(share,
                                         args.force,
                                         args.name,
                                         args.description)
    _print_share_snapshot(cs, snapshot)


@utils.arg('share',
           metavar='<share>',
           help='Name or ID of the share to rename.')
@utils.arg('name',
           nargs='?',
           metavar='<name>',
           help='New name for the share.')
@utils.arg('--description', metavar='<description>',
           help='Optional share description. (Default=None)',
           default=None)
@utils.service_type('share')
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


@utils.arg('snapshot',
           metavar='<snapshot>',
           help='Name or ID of the snapshot to rename.')
@utils.arg('name',
           nargs='?',
           metavar='<name>',
           help='New name for the snapshot.')
@utils.arg('--description', metavar='<description>',
           help='Optional snapshot description. (Default=None)',
           default=None)
@utils.service_type('share')
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


@utils.arg(
    'snapshot',
    metavar='<snapshot>',
    help='Name or ID of the snapshot to delete.')
@utils.service_type('share')
def do_snapshot_delete(cs, args):
    """Remove a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.delete()


@utils.arg('snapshot', metavar='<snapshot>',
           help='Name or ID of the snapshot to modify.')
@utils.arg('--state', metavar='<state>',
           default='available',
           help=('Indicate which state to assign the snapshot. '
                 'Options include available, error, creating, deleting, '
                 'error_deleting. If no state is provided, '
                 'available will be used.'))
@utils.service_type('share')
def do_snapshot_reset_state(cs, args):
    """Explicitly update the state of a snapshot."""
    snapshot = _find_share_snapshot(cs, args.snapshot)
    snapshot.reset_state(args.state)


@utils.arg(
    'share',
    metavar='<share>',
    help='Name or ID of the share to modify.')
@utils.arg(
    '--state',
    metavar='<state>',
    default='available',
    help=('Indicate which state to assign the share. Options include '
          'available, error, creating, deleting, error_deleting. If no '
          'state is provided, available will be used.'))
@utils.service_type('share')
def do_reset_state(cs, args):
    """Explicitly update the state of a share."""
    share = _find_share(cs, args.share)
    share.reset_state(args.state)


@utils.arg(
    '--neutron-net-id',
    metavar='neutron-net-id',
    default=None,
    help="Neutron network id. Used to set up network for share servers.")
@utils.arg(
    '--neutron-subnet-id',
    metavar='neutron-subnet-id',
    default=None,
    help="Neutron subnet id. Used to set up network for share servers. "
         "This subnet should belong to specified neutron network.")
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Share network name.")
@utils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Share network description.")
def do_share_network_create(cs, args):
    """Create description for network used by the tenant"""
    values = {'neutron_net_id': args.neutron_net_id,
              'neutron_subnet_id': args.neutron_subnet_id,
              'name': args.name,
              'description': args.description}
    share_network = cs.share_networks.create(**values)
    info = share_network._info.copy()
    utils.print_dict(info)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of share network to update.')
@utils.arg(
    '--neutron-net-id',
    metavar='neutron-net-id',
    default=None,
    help="Neutron network id. Used to set up network for share servers.")
@utils.arg(
    '--neutron-subnet-id',
    metavar='neutron-subnet-id',
    default=None,
    help="Neutron subnet id. Used to set up network for share servers. "
         "This subnet should belong to specified neutron network.")
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="Share network name.")
@utils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="Share network description.")
def do_share_network_update(cs, args):
    """Update share network data"""
    values = {'neutron_net_id': args.neutron_net_id,
              'neutron_subnet_id': args.neutron_subnet_id,
              'name': args.name,
              'description': args.description}
    share_network = _find_share_network(cs, args.share_network)\
        .update(**values)
    info = share_network._info.copy()
    utils.print_dict(info)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of the share network to show.')
def do_share_network_show(cs, args):
    """Get a description for network used by the tenant"""
    share_network = _find_share_network(cs, args.share_network)
    info = share_network._info.copy()
    utils.print_dict(info)


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
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
def do_share_network_list(cs, args):
    """Get a list of network info"""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'status': args.status,
    }
    share_networks = cs.share_networks.list(search_opts=search_opts)
    fields = ['id', 'name', 'status']
    utils.print_list(share_networks, fields=fields)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
@utils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service to associate with.')
def do_share_network_security_service_add(cs, args):
    """Associate security service with share network"""
    share_network = _find_share_network(cs, args.share_network)
    cs.share_networks.add_security_service(share_network,
                                           args.security_service)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
@utils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service to dissociate.')
def do_share_network_security_service_remove(cs, args):
    """Dissociate security service from share network"""
    share_network = _find_share_network(cs, args.share_network)
    cs.share_networks.remove_security_service(share_network,
                                              args.security_service)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Share network name or ID.')
def do_share_network_security_service_list(cs, args):
    """Get a list of security services associated with a given share network"""
    share_network = _find_share_network(cs, args.share_network)
    search_opts = {
        'share_network_id': share_network.id,
    }
    security_services = cs.security_services.list(search_opts=search_opts)
    fields = ['id', 'name', 'status', 'type', ]
    utils.print_list(security_services, fields=fields)


@utils.arg(
    'share_network',
    metavar='<share-network>',
    help='Name or ID of share network to be deleted.')
def do_share_network_delete(cs, args):
    """Delete share network"""
    _find_share_network(cs, args.share_network).delete()


@utils.arg(
    'type',
    metavar='<type>',
    help="Security service type: 'ldap', 'kerberos' or 'active_directory'")
@utils.arg(
    '--dns-ip',
    metavar='<dns_ip>',
    default=None,
    help="dns ip address used inside tenant's network")
@utils.arg(
    '--server',
    metavar='<server>',
    default=None,
    help="security service ip address or hostname")
@utils.arg(
    '--domain',
    metavar='<domain>',
    default=None,
    help="security service domain")
@utils.arg(
    '--sid',
    metavar='<security identifier>',
    default=None,
    help="security service user or group used by tenant")
@utils.arg(
    '--password',
    metavar='<password>',
    default=None,
    help="password used by sid")
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="security service name")
@utils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="security service description")
def do_security_service_create(cs, args):
    """Create security service used by tenant"""
    values = {'dns_ip': args.dns_ip,
              'server': args.server,
              'domain': args.domain,
              'sid': args.sid,
              'password': args.password,
              'name': args.name,
              'description': args.description}
    security_service = cs.security_services.create(args.type, **values)
    info = security_service._info.copy()
    utils.print_dict(info)


@utils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service to update.')
@utils.arg(
    '--dns-ip',
    metavar='<dns-ip>',
    default=None,
    help="dns ip address used inside tenant's network")
@utils.arg(
    '--server',
    metavar='<server>',
    default=None,
    help="security service ip address or hostname")
@utils.arg(
    '--domain',
    metavar='<domain>',
    default=None,
    help="security service domain")
@utils.arg(
    '--sid',
    metavar='<security identifier>',
    default=None,
    help="security service user or group used by tenant")
@utils.arg(
    '--password',
    metavar='<password>',
    default=None,
    help="password used by sid")
@utils.arg(
    '--name',
    metavar='<name>',
    default=None,
    help="security service name")
@utils.arg(
    '--description',
    metavar='<description>',
    default=None,
    help="security service description")
def do_security_service_update(cs, args):
    """Update security service"""
    values = {'dns_ip': args.dns_ip,
              'server': args.server,
              'domain': args.domain,
              'sid': args.sid,
              'password': args.password,
              'name': args.name,
              'description': args.description}
    security_service = cs.security_services.update(args.security_service,
                                                   **values)
    info = security_service._info.copy()
    utils.print_dict(info)


@utils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service to show.')
def do_security_service_show(cs, args):
    """Show security service"""
    security_service = cs.security_services.get(args.security_service)
    info = security_service._info.copy()
    utils.print_dict(info)


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
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
def do_security_service_list(cs, args):
    """Get a list of security services"""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))
    search_opts = {
        'all_tenants': all_tenants,
        'status': args.status,
    }
    security_services = cs.security_services.list(search_opts=search_opts)
    fields = ['id', 'name', 'status', 'type', ]
    utils.print_list(security_services, fields=fields)


@utils.arg(
    'security_service',
    metavar='<security-service>',
    help='Security service to delete.')
def do_security_service_delete(cs, args):
    """Delete security service"""
    cs.security_services.delete(args.security_service)


@utils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help='Filter results by name of host.')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status.')
@utils.arg(
    '--share-network',
    metavar='<share_network>',
    default=None,
    help='Filter results by share network.')
@utils.arg(
    '--project-id',
    metavar='<project_id>',
    default=None,
    help='Filter results by project id.')
def do_share_server_list(cs, args):
    """List all the share servers."""
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


@utils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='Id of share server.')
def do_share_server_show(cs, args):
    """Show share server info."""
    share_server = cs.share_servers.get(args.id)
    # All 'backend_details' data already present as separated strings,
    # so remove big dict from view.
    if "backend_details" in share_server._info:
        del share_server._info["backend_details"]
    utils.print_dict(share_server._info)


@utils.arg(
    'id',
    metavar='<id>',
    type=str,
    help='Id of share server.')
def do_share_server_details(cs, args):
    """Show share server details."""
    details = cs.share_servers.details(args.id)
    utils.print_dict(details._info)


@utils.arg(
    '--host',
    metavar='<hostname>',
    default=None,
    help='Name of host.')
@utils.arg(
    '--binary',
    metavar='<binary>',
    default=None,
    help='Service binary.')
@utils.arg(
    '--status',
    metavar='<status>',
    default=None,
    help='Filter results by status')
@utils.arg(
    '--state',
    metavar='<state>',
    default=None,
    help='Filter results by state')
@utils.arg(
    '--zone',
    metavar='<zone>',
    default=None,
    help='Availability zone.')
def do_service_list(cs, args):
    """List all the services."""
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
    return utils.find_resource(cs.volume_types, vtype)


@utils.service_type('share')
def do_type_list(cs, args):
    """Print a list of available 'volume types'."""
    vtypes = cs.volume_types.list()
    _print_volume_type_list(vtypes)


@utils.service_type('share')
def do_extra_specs_list(cs, args):
    """Print a list of current 'volume types and extra specs' (Admin Only)."""
    vtypes = cs.volume_types.list()
    _print_type_and_extra_specs_list(vtypes)


@utils.arg('name',
           metavar='<name>',
           help="Name of the new volume type")
@utils.service_type('share')
def do_type_create(cs, args):
    """Create a new volume type."""
    vtype = cs.volume_types.create(args.name)
    _print_volume_type_list([vtype])


@utils.arg('id',
           metavar='<id>',
           help="Name or ID of the volume type to delete")
@utils.service_type('share')
def do_type_delete(cs, args):
    """Delete a specific volume type."""
    volume_type = _find_volume_type(cs, args.id)
    cs.volume_types.delete(volume_type)


@utils.arg('vtype',
           metavar='<vtype>',
           help="Name or ID of the volume type")
@utils.arg('action',
           metavar='<action>',
           choices=['set', 'unset'],
           help="Actions: 'set' or 'unset'")
@utils.arg('metadata',
           metavar='<key=value>',
           nargs='*',
           default=None,
           help='Extra_specs to set/unset (only key is necessary on unset)')
@utils.service_type('share')
def do_type_key(cs, args):
    """Set or unset extra_spec for a volume type."""
    vtype = _find_volume_type(cs, args.vtype)

    if args.metadata is not None:
        keypair = _extract_metadata(args)

        if args.action == 'set':
            vtype.set_keys(keypair)
        elif args.action == 'unset':
            vtype.unset_keys(list(keypair))
