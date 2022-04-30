# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from manilaclient import api_versions
from manilaclient import base
from manilaclient.common import constants

RESOURCES_NAME = 'share_backups'
RESOURCE_NAME = 'share_backup'
RESOURCES_PATH = '/share-backups'
RESOURCE_PATH = '/share-backups/%s'
RESOURCE_PATH_ACTION = '/share-backups/%s/action'


class ShareBackup(base.Resource):
    def __repr__(self):
        return "<Share Backup: %s>" % self.id


class ShareBackupManager(base.ManagerWithFind):
    """Manage :class:`ShareBackup` resources."""
    resource_class = ShareBackup

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def get(self, backup):
        """Get a share backup.

        :param backup: either backup object or its UUID.
        :rtype: :class:`ShareBackup`
        """
        backup_id = base.getid(backup)
        return self._get(RESOURCE_PATH % backup_id, RESOURCE_NAME)

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def list(self, detailed=True, search_opts=None, sort_key=None,
             sort_dir=None):
        """List all share backups or list backups belonging to a share.

        :param detailed: list backups with detailed fields.
        :param search_opts: Search options to filter out shares.
        :param sort_key: Key to be sorted.
        :param sort_dir: Sort direction, should be 'desc' or 'asc'.
        :rtype: list of :class:`ShareBackup`
        """

        search_opts = search_opts or {}

        if sort_key is not None:
            if sort_key in constants.BACKUP_SORT_KEY_VALUES:
                search_opts['sort_key'] = sort_key
            else:
                raise ValueError(
                    'sort_key must be one of the following: %s.'
                    % ', '.join(constants.BACKUP_SORT_KEY_VALUES))

        if sort_dir is not None:
            if sort_dir in constants.SORT_DIR_VALUES:
                search_opts['sort_dir'] = sort_dir
            else:
                raise ValueError(
                    'sort_dir must be one of the following: %s.'
                    % ', '.join(constants.SORT_DIR_VALUES))

        query_string = self._build_query_string(search_opts)
        if detailed:
            path = "/share-backups/detail%s" % (query_string,)
        else:
            path = "/share-backups%s" % (query_string,)

        return self._list(path, 'share_backups')

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def create(self, share, backup_options=None, description=None, name=None):
        """Create a backup for a share.

        :param share: The share to create the backup of. Can be the share
        object or its UUID.
        :param backup_options: dict - custom set of key-values
        :param name: text - name of new share
        :param description: - description for new share
        """
        share_id = base.getid(share)
        body = {
            'share_id': share_id,
            'backup_options': backup_options,
            'description': description,
            'name': name,
        }

        return self._create(RESOURCES_PATH,
                            {RESOURCE_NAME: body},
                            RESOURCE_NAME)

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def delete(self, backup):
        backup_id = base.getid(backup)
        url = RESOURCE_PATH % backup_id
        self._delete(url)

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def restore(self, backup):
        return self._action('restore', backup)

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def reset_status(self, backup, state):
        return self._action('reset_status', backup, {"status": state})

    @api_versions.wraps("2.80")
    @api_versions.experimental_api
    def update(self, backup, **kwargs):
        if not kwargs:
            return
        backup_id = base.getid(backup)
        body = {'share_backup': kwargs}
        return self._update(RESOURCE_PATH % backup_id, body)

    def _action(self, action, backup, info=None, **kwargs):
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        backup_id = base.getid(backup)
        url = RESOURCE_PATH_ACTION % backup_id
        return self.api.client.post(url, body=body)
