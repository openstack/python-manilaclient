# Copyright (c) 2011 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Share Type interface.
"""

from manilaclient import api_versions
from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base


class ShareType(common_base.Resource):
    """A Share Type is the type of share to be created."""

    def __init__(self, manager, info, loaded=False):
        super(ShareType, self).__init__(manager, info, loaded)
        self._required_extra_specs = info.get('required_extra_specs', {})
        self._optional_extra_specs = {
            'snapshot_support': info.get('extra_specs', {}).get(
                'snapshot_support', 'unknown'),
        }

    def __repr__(self):
        return "<ShareType: %s>" % self.name

    @property
    def is_public(self):
        """Provide a user-friendly accessor to [os-]share-type-access."""
        return self._info.get(
            "share_type_access:is_public",
            self._info.get("os-share-type-access:is_public", "N/A"))

    def get_keys(self, prefer_resource_data=True):
        """Get extra specs from a share type.

        :param prefer_resource_data: By default extra_specs are retrieved from
        resource data, but user can force this method to make API call.
        :return: dict with extra specs
        """
        extra_specs = getattr(self, 'extra_specs', None)

        if prefer_resource_data and extra_specs:
            return extra_specs

        _resp, body = self.manager.api.client.get(
            "/types/%s/extra_specs" % common_base.getid(self))

        self.extra_specs = body["extra_specs"]

        return body["extra_specs"]

    def get_required_keys(self):
        return self._required_extra_specs

    def get_optional_keys(self):
        return self._optional_extra_specs

    def set_keys(self, metadata):
        """Set extra specs on a share type.

        :param type : The :class:`ShareType` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
            "/types/%s/extra_specs" % common_base.getid(self),
            body,
            "extra_specs",
            return_raw=True,
        )

    def unset_keys(self, keys):
        """Unset extra specs on a share type.

        :param type_id: The :class:`ShareType` to unset extra spec on
        :param keys: A list of keys to be unset
        """

        # NOTE(jdg): This wasn't actually doing all of the keys before
        # the return in the loop resulted in ony ONE key being unset.
        # since on success the return was NONE, we'll only interrupt the loop
        # and return if there's an error
        resp = None
        for k in keys:
            resp = self.manager._delete(
                "/types/%s/extra_specs/%s" % (common_base.getid(self), k))
            if resp is not None:
                return resp


class ShareTypeManager(base.ManagerWithFind):
    """Manage :class:`ShareType` resources."""

    resource_class = ShareType

    def list(self, search_opts=None, show_all=True):
        """Get a list of all share types.

        :rtype: list of :class:`ShareType`.
        """
        query_string = ''
        if show_all:
            query_string = '?is_public=all'
        return self._list("/types%s" % query_string, "share_types")

    def get(self, share_type="default"):
        """Get a specific share type.

        :param share_type: The ID of the :class:`ShareType` to get.
        :rtype: :class:`ShareType`
        """
        return self._get("/types/%s" % common_base.getid(share_type),
                         "share_type")

    def delete(self, share_type):
        """Delete a specific share_type.

        :param share_type: The name or ID of the :class:`ShareType` to get.
        """
        self._delete("/types/%s" % common_base.getid(share_type))

    def _do_create(self, name, spec_driver_handles_share_servers,
                   spec_snapshot_support=True, is_public=True,
                   is_public_keyname="os-share-type-access:is_public"):
        """Create a share type.

        :param name: Descriptive name of the share type
        :rtype: :class:`ShareType`
        """

        body = {
            "share_type": {
                "name": name,
                is_public_keyname: is_public,
                "extra_specs": {
                    "driver_handles_share_servers":
                        spec_driver_handles_share_servers,
                    "snapshot_support": spec_snapshot_support,
                },
            }
        }

        return self._create("/types", body, "share_type")

    @api_versions.wraps("1.0", "2.6")
    def create(self, name, spec_driver_handles_share_servers,
               spec_snapshot_support=True, is_public=True):
        return self._do_create(
            name,
            spec_driver_handles_share_servers,
            spec_snapshot_support,
            is_public,
            "os-share-type-access:is_public")

    @api_versions.wraps("2.7")  # noqa
    def create(self, name, spec_driver_handles_share_servers,
               spec_snapshot_support=True, is_public=True):
        return self._do_create(
            name,
            spec_driver_handles_share_servers,
            spec_snapshot_support,
            is_public,
            "share_type_access:is_public")
