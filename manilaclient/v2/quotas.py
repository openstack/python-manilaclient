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

from manilaclient import api_versions
from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base

RESOURCE_PATH_LEGACY = '/os-quota-sets'
RESOURCE_PATH = '/quota-sets'


class QuotaSet(common_base.Resource):

    @property
    def id(self):
        """Needed by Resource to self-refresh and be indexed."""
        return self.tenant_id

    def update(self, *args, **kwargs):
        self.manager.update(self.tenant_id, *args, **kwargs)


class QuotaSetManager(base.ManagerWithFind):
    resource_class = QuotaSet

    def _do_get(self, tenant_id, user_id=None, resource_path=RESOURCE_PATH):
        if hasattr(tenant_id, 'tenant_id'):
            tenant_id = tenant_id.tenant_id
        data = {
            "resource_path": resource_path,
            "tenant_id": tenant_id,
            "user_id": user_id,
        }
        if user_id:
            url = "%(resource_path)s/%(tenant_id)s?user_id=%(user_id)s" % data
        else:
            url = "%(resource_path)s/%(tenant_id)s" % data
        return self._get(url, "quota_set")

    @api_versions.wraps("1.0", "2.6")
    def get(self, tenant_id, user_id=None):
        return self._do_get(tenant_id, user_id, RESOURCE_PATH_LEGACY)

    @api_versions.wraps("2.7")  # noqa
    def get(self, tenant_id, user_id=None):
        return self._do_get(tenant_id, user_id, RESOURCE_PATH)

    def _do_update(self, tenant_id, shares=None, snapshots=None,
                   gigabytes=None, snapshot_gigabytes=None,
                   share_networks=None, force=None, user_id=None,
                   resource_path=RESOURCE_PATH):

        body = {
            'quota_set': {
                'tenant_id': tenant_id,
                'shares': shares,
                'snapshots': snapshots,
                'gigabytes': gigabytes,
                'snapshot_gigabytes': snapshot_gigabytes,
                'share_networks': share_networks,
                'force': force,
            },
        }

        for key in list(body['quota_set']):
            if body['quota_set'][key] is None:
                body['quota_set'].pop(key)
        data = {
            "resource_path": resource_path,
            "tenant_id": tenant_id,
            "user_id": user_id,
        }
        if user_id:
            url = '%(resource_path)s/%(tenant_id)s?user_id=%(user_id)s' % data
        else:
            url = "%(resource_path)s/%(tenant_id)s" % data

        return self._update(url, body, 'quota_set')

    @api_versions.wraps("1.0", "2.6")
    def update(self, tenant_id, shares=None, snapshots=None, gigabytes=None,
               snapshot_gigabytes=None, share_networks=None, force=None,
               user_id=None):
        return self._do_update(
            tenant_id, shares, snapshots, gigabytes, snapshot_gigabytes,
            share_networks, force, user_id, RESOURCE_PATH_LEGACY,
        )

    @api_versions.wraps("2.7")  # noqa
    def update(self, tenant_id, shares=None, snapshots=None, gigabytes=None,
               snapshot_gigabytes=None, share_networks=None, force=None,
               user_id=None):
        return self._do_update(
            tenant_id, shares, snapshots, gigabytes, snapshot_gigabytes,
            share_networks, force, user_id, RESOURCE_PATH,
        )

    @api_versions.wraps("1.0", "2.6")
    def defaults(self, tenant_id):
        return self._get(
            "%(resource_path)s/%(tenant_id)s/defaults" % {
                "resource_path": RESOURCE_PATH_LEGACY, "tenant_id": tenant_id},
            "quota_set")

    @api_versions.wraps("2.7")  # noqa
    def defaults(self, tenant_id):
        return self._get(
            "%(resource_path)s/%(tenant_id)s/defaults" % {
                "resource_path": RESOURCE_PATH, "tenant_id": tenant_id},
            "quota_set")

    def _do_delete(self, tenant_id, user_id=None, resource_path=RESOURCE_PATH):
        data = {
            "resource_path": resource_path,
            "tenant_id": tenant_id,
            "user_id": user_id,
        }
        if user_id:
            url = '%(resource_path)s/%(tenant_id)s?user_id=%(user_id)s' % data
        else:
            url = '%(resource_path)s/%(tenant_id)s' % data
        self._delete(url)

    @api_versions.wraps("1.0", "2.6")
    def delete(self, tenant_id, user_id=None):
        return self._do_delete(
            tenant_id, user_id, resource_path=RESOURCE_PATH_LEGACY)

    @api_versions.wraps("2.7")  # noqa
    def delete(self, tenant_id, user_id=None):
        return self._do_delete(tenant_id, user_id, resource_path=RESOURCE_PATH)
