# Copyright 2013 OpenStack Foundation
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

RESOURCE_PATH_LEGACY = '/os-quota-class-sets'
RESOURCE_PATH = '/quota-class-sets'
REPLICA_QUOTAS_MICROVERSION = "2.53"


class QuotaClassSet(base.Resource):

    @property
    def id(self):
        """Needed by base.Resource to self-refresh and be indexed."""
        return self.class_name

    def update(self, *args, **kwargs):
        self.manager.update(self.class_name, *args, **kwargs)


class QuotaClassSetManager(base.ManagerWithFind):
    resource_class = QuotaClassSet

    @api_versions.wraps("1.0", "2.6")
    def get(self, class_name):
        return self._get(
            "%(resource_path)s/%(class_name)s" % {
                "resource_path": RESOURCE_PATH_LEGACY,
                "class_name": class_name},
            "quota_class_set")

    @api_versions.wraps("2.7")  # noqa
    def get(self, class_name):  # noqa
        return self._get(
            "%(resource_path)s/%(class_name)s" % {
                "resource_path": RESOURCE_PATH, "class_name": class_name},
            "quota_class_set")

    def _do_update(self, class_name, shares=None, gigabytes=None,
                   snapshots=None, snapshot_gigabytes=None,
                   share_networks=None, share_replicas=None,
                   replica_gigabytes=None, per_share_gigabytes=None,
                   share_groups=None, share_group_snapshots=None,
                   resource_path=RESOURCE_PATH):
        body = {
            'quota_class_set': {
                'class_name': class_name,
                'shares': shares,
                'snapshots': snapshots,
                'gigabytes': gigabytes,
                'snapshot_gigabytes': snapshot_gigabytes,
                'share_networks': share_networks,
                "share_replicas": share_replicas,
                "replica_gigabytes": replica_gigabytes,
                'per_share_gigabytes': per_share_gigabytes,
                'share_groups': share_groups,
                'share_group_snapshots': share_group_snapshots,
            }
        }

        for key in list(body['quota_class_set']):
            if body['quota_class_set'][key] is None:
                body['quota_class_set'].pop(key)

        self._update(
            "%(resource_path)s/%(class_name)s" % {
                "resource_path": resource_path,
                "class_name": class_name},
            body)

    @api_versions.wraps("1.0", "2.6")
    def update(self, class_name, shares=None, gigabytes=None,
               snapshots=None, snapshot_gigabytes=None, share_networks=None):
        return self._do_update(
            class_name, shares=shares, gigabytes=gigabytes,
            snapshots=snapshots, snapshot_gigabytes=snapshot_gigabytes,
            share_networks=share_networks, resource_path=RESOURCE_PATH_LEGACY)

    @api_versions.wraps("2.7", "2.39")  # noqa
    def update(self, class_name, shares=None, gigabytes=None,  # noqa
               snapshots=None, snapshot_gigabytes=None, share_networks=None):
        return self._do_update(
            class_name, shares=shares, gigabytes=gigabytes,
            snapshots=snapshots, snapshot_gigabytes=snapshot_gigabytes,
            share_networks=share_networks, resource_path=RESOURCE_PATH)

    @api_versions.wraps("2.40", "2.52")  # noqa
    def update(self, class_name, shares=None, gigabytes=None,  # noqa
               snapshots=None, snapshot_gigabytes=None, share_networks=None,
               share_groups=None, share_group_snapshots=None):
        return self._do_update(
            class_name, shares=shares, gigabytes=gigabytes,
            snapshots=snapshots, snapshot_gigabytes=snapshot_gigabytes,
            share_networks=share_networks, share_groups=share_groups,
            share_group_snapshots=share_group_snapshots,
            resource_path=RESOURCE_PATH)

    @api_versions.wraps(REPLICA_QUOTAS_MICROVERSION, "2.61")  # noqa
    def update(self, class_name, shares=None, gigabytes=None,  # noqa
               snapshots=None, snapshot_gigabytes=None, share_networks=None,
               share_groups=None, share_group_snapshots=None,
               share_replicas=None, replica_gigabytes=None):
        return self._do_update(
            class_name, shares=shares, gigabytes=gigabytes,
            snapshots=snapshots, snapshot_gigabytes=snapshot_gigabytes,
            share_networks=share_networks, share_groups=share_groups,
            share_group_snapshots=share_group_snapshots,
            share_replicas=share_replicas, replica_gigabytes=replica_gigabytes,
            resource_path=RESOURCE_PATH)

    @api_versions.wraps("2.62")  # noqa
    def update(self, class_name, shares=None, gigabytes=None,  # noqa
               snapshots=None, snapshot_gigabytes=None, share_networks=None,
               share_groups=None, share_group_snapshots=None,
               share_replicas=None, replica_gigabytes=None,
               per_share_gigabytes=None):
        return self._do_update(
            class_name, shares=shares, gigabytes=gigabytes,
            snapshots=snapshots, snapshot_gigabytes=snapshot_gigabytes,
            share_networks=share_networks, share_groups=share_groups,
            share_group_snapshots=share_group_snapshots,
            share_replicas=share_replicas,
            replica_gigabytes=replica_gigabytes,
            per_share_gigabytes=per_share_gigabytes,
            resource_path=RESOURCE_PATH)
