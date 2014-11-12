The :mod:`manilaclient` Python API
==================================

.. module:: manilaclient
   :synopsis: A client for the OpenStack Manila API.

.. currentmodule:: manilaclient

Usage
=====

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
    >>>share.delete

