# Copyright (c) 2022 China Telecom Digital Intelligence.
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
from manilaclient.common import constants


class ShareTransfer(base.Resource):
    """Transfer a share from one tenant to another"""

    def __repr__(self):
        return "<ShareTransfer: %s>" % self.id

    def delete(self):
        """Delete this share transfer."""
        return self.manager.delete(self)


class ShareTransferManager(base.ManagerWithFind):
    """Manage :class:`ShareTransfer` resources."""
    resource_class = ShareTransfer

    @api_versions.wraps(constants.SHARE_TRANSFER_VERSION)
    def create(self, share_id, name=None):
        """Creates a share transfer.

        :param share_id: The ID of the share to transfer.
        :param name: The name of the transfer.
        :rtype: :class:`ShareTransfer`
        """
        body = {'transfer': {'share_id': share_id,
                             'name': name}}

        return self._create('/share-transfers', body, 'transfer')

    @api_versions.wraps(constants.SHARE_TRANSFER_VERSION)
    def accept(self, transfer, auth_key, clear_access_rules=False):
        """Accept a share transfer.

        :param transfer_id: The ID of the transfer to accept.
        :param auth_key: The auth_key of the transfer.
        :param clear_access_rules: Transfer share without access rules
        :rtype: :class:`ShareTransfer`
        """
        transfer_id = base.getid(transfer)
        body = {'accept': {'auth_key': auth_key,
                           'clear_access_rules': clear_access_rules}}

        self._accept('/share-transfers/%s/accept' % transfer_id, body)

    @api_versions.wraps(constants.SHARE_TRANSFER_VERSION)
    def get(self, transfer_id):
        """Show details of a share transfer.

        :param transfer_id: The ID of the share transfer to display.
        :rtype: :class:`ShareTransfer`
        """
        return self._get("/share-transfers/%s" % transfer_id, "transfer")

    @api_versions.wraps(constants.SHARE_TRANSFER_VERSION)
    def list(self, detailed=True, search_opts=None,
             sort_key=None, sort_dir=None):
        """Get a list of all share transfer.

        :param detailed: Get detailed object information.
        :param search_opts: Filtering options.
        :param sort_key: Key to be sorted (i.e. 'created_at').
        :param sort_dir: Sort direction, should be 'desc' or 'asc'.
        :rtype: list of :class:`ShareTransfer`
        """
        if search_opts is None:
            search_opts = {}

        if sort_key is not None:
            if sort_key in constants.SHARE_TRANSFER_SORT_KEY_VALUES:
                search_opts['sort_key'] = sort_key
                # NOTE: Replace aliases with appropriate keys
                if sort_key == 'name':
                    search_opts['sort_key'] = 'display_name'
            else:
                raise ValueError(
                    'sort_key must be one of the following: %s.'
                    % ', '.join(constants.SHARE_TRANSFER_SORT_KEY_VALUES))

        if sort_dir is not None:
            if sort_dir in constants.SORT_DIR_VALUES:
                search_opts['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(constants.SORT_DIR_VALUES))

        query_string = self._build_query_string(search_opts)

        if detailed:
            path = "/share-transfers/detail%s" % (query_string,)
        else:
            path = "/share-transfers%s" % (query_string,)

        return self._list(path, 'transfers')

    @api_versions.wraps(constants.SHARE_TRANSFER_VERSION)
    def delete(self, transfer_id):
        """Delete a share transfer.

        :param transfer_id: The :class:`ShareTransfer` to delete.
        """

        return self._delete("/share-transfers/%s" % base.getid(transfer_id))
