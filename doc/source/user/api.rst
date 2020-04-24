The :program:`manilaclient` Python API
======================================

.. module:: manilaclient
   :synopsis: A client for the OpenStack Manila API.

.. currentmodule:: manilaclient

Usage
-----

In order to use the Python API directly, you must first obtain an auth
token and identify which endpoint you wish to speak to. Once you have
done so, you can use the API like so::

    >>> from manilaclient import client
    >>> manila = client.Client('1', $OS_USER_NAME, $OS_PASSWORD, $OS_TENANT_NAME, $OS_AUTH_URL)
    >>> manila.shares.list()
    []
    >>> share = manila.shares.create(share_proto="nfs", size=1, share_network_id="some_share_network_id")
    >>> share.id
    ce06d0a8-5c1b-4e2c-81d2-39eca6bbfb70
    >>> manila.shares.list()
    [<Share: ce06d0a8-5c1b-4e2c-81d2-39eca6bbfb70>]
    >>> share.delete

In addition to creating and deleting shares, the manilaclient can manage
share-types, access controls, and more! Using CephFS with Ganesha for NFS
support as an example (assuumes this continues from the above initialization)::

    >>> share_type = client.share_types.create(
    >>>     name="cephfsnfstype", spec_driver_handles_share_servers=False,
    >>>     extra_specs={
    >>>         'vendor_name': 'Ceph',
    >>>         'storage_protocol': 'NFS',
    >>>         'snapshot_support': False,
    >>>     })
    >>> share_type
    <ShareType: cephfsnfstype>
    >>> share = client.shares.create(
    >>>     share_type='cephfsnfstype', name='cephnfsshare1',
    >>>     share_proto="nfs", size=1)
    >>> share.allow(access_type='ip', access="192.168.0.0/24", access_level='rw')
    {'id': '29bc4b66-d55d-424d-8107-aee96d1c562b', 'share_id': '0ac95dd2-afba-4ba3-8934-721b29492f04', 'access_level': 'rw', 'access_to': '192.168.0.0/24', 'access_type': 'ip', 'state': 'new'}
    >>> share.export_locations
    ['10.5.0.22:/volumes/_nogroup/cf0451b6-0a95-4982-a801-2e212e9c9b96']

In the above example, Manila will be setup with an NFS share type, backed
by CephFS. A share is then created, and then access controls are added giving
the 192.168.0/24 subnet read/write access to the share.
