# Copyright (c) 2025 Cloudification GmbH.
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
Qos Type interface.
"""

from manilaclient import api_versions
from manilaclient import base
from manilaclient.common import constants


class QosType(base.Resource):
    """A Qos Type represents Quality of service of Manila resource."""

    def __init__(self, manager, info, loaded=False):
        super().__init__(manager, info, loaded)
        self._specs = info.get('specs', {})

    def __repr__(self):
        return f"<QosType: {self.name}>"

    def get_keys(self, prefer_resource_data=True):
        """Get specs from a qos type.

        :param prefer_resource_data: By default specs are retrieved from
        resource data, but user can force this method to make API call.
        :return: dict with specs
        """
        specs = getattr(self, 'specs', None)

        if prefer_resource_data and specs:
            return specs

        qos_type_id = base.getid(self)
        _resp, body = self.manager.api.client.get(
            f"/qos-types/{qos_type_id}/specs"
        )

        self.specs = body["specs"]

        return body["specs"]

    def set_keys(self, metadata):
        """Set specs on a qos type.

        :param metadata: A dict of key/value pairs to be set
        """
        body = {'specs': metadata}
        qos_type_id = base.getid(self)
        return self.manager._create(
            f"/qos-types/{qos_type_id}/specs",
            body,
            "specs",
            return_raw=True,
        )

    def unset_keys(self, keys):
        """Unset specs on a qos type.

        :param keys: A list of keys to be unset
        """
        qos_type_id = base.getid(self)
        for k in keys:
            self.manager._delete(f"/qos-types/{qos_type_id}/specs/{k}")

    def update(self, **kwargs):
        """Update this qos type."""
        return self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this qos type."""
        return self.manager.delete(self)


class QosTypeManager(base.ManagerWithFind):
    """Manage :class:`QosType` resources."""

    resource_class = QosType

    @api_versions.wraps(constants.QOS_TYPE_VERSION)
    def list(self, search_opts=None, sort_key=None, sort_dir=None):
        """Get a list of all qos types.

        :param search_opts: Search options to filter out qos types.
        :param sort_key: Key to be sorted.
        :param sort_dir: Sort direction, should be 'desc' or 'asc'.
        :rtype: list of :class:`QosType`.
        """
        search_opts = search_opts or {}

        if sort_key is not None:
            if sort_key in constants.QOS_TYPE_SORT_KEY_VALUES:
                search_opts['sort_key'] = sort_key
            else:
                raise ValueError(
                    'sort_key must be one of the following: {}.'.format(
                        ', '.join(constants.QOS_TYPE_SORT_KEY_VALUES)
                    )
                )

        if sort_dir is not None:
            if sort_dir in constants.SORT_DIR_VALUES:
                search_opts['sort_dir'] = sort_dir
            else:
                raise ValueError(
                    'sort_dir must be one of the following: {}.'.format(
                        ', '.join(constants.SORT_DIR_VALUES)
                    )
                )

        query_string = self._build_query_string(search_opts)
        return self._list(f"/qos-types{query_string}", "qos_types")

    @api_versions.wraps(constants.QOS_TYPE_VERSION)
    def get(self, qos_type):
        """Get a specific qos type.

        :param qos_type: The ID of the :class:`QosType` to get.
        :rtype: :class:`QosType`
        """
        qos_type_id = base.getid(qos_type)
        return self._get(f"/qos-types/{qos_type_id}", "qos_type")

    @api_versions.wraps(constants.QOS_TYPE_VERSION)
    def delete(self, qos_type):
        """Delete a specific qos_type.

        :param qos_type: The name or ID of the :class:`QosType` to get.
        """
        qos_type_id = base.getid(qos_type)
        self._delete(f"/qos-types/{qos_type_id}")

    @api_versions.wraps(constants.QOS_TYPE_VERSION)
    def create(self, name, description=None, specs=None):
        """Create a qos type.

        :param name: Descriptive name of the qos type
        :param specs: Specs of the qos type
        :rtype: :class:`QosType`
        """
        if specs is None:
            specs = {}

        body = {
            "qos_type": {
                "name": name,
                "specs": specs,
            }
        }

        if description:
            body["qos_type"]["description"] = description
        return self._create("/qos-types", body, "qos_type")

    @api_versions.wraps(constants.QOS_TYPE_VERSION)
    def update(self, qos_type, **kwargs):
        """Update the description for a qos type.

        :param qos_type: the ID of the :class: `QosType` to update.
        :param description: Description of the qos type.
        :rtype: :class:`QosType`
        """

        if not kwargs:
            return

        body = {
            'qos_type': kwargs,
        }
        qos_type_id = base.getid(qos_type)
        return self._update(f"/qos-types/{qos_type_id}", body, "qos_type")
