# Copyright 2014 OpenStack Foundation.
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

RESOURCES_NAME = 'share_servers'
RESOURCES_PATH = '/share-servers'
RESOURCE_PATH = RESOURCES_PATH + '/%s'
RESOURCE_NAME = 'share_server'
ACTION_PATH = RESOURCE_PATH + '/action'


class ShareServer(base.Resource):

    def __repr__(self):
        return "<ShareServer: %s>" % self.id

    def __getattr__(self, attr):
        if attr == 'share_network':
            attr = 'share_network_name'
        return super(ShareServer, self).__getattr__(attr)

    def delete(self):
        """Delete this share server."""
        self.manager.delete(self)

    def unmanage(self, force=False):
        """Unmanage this share server."""
        self.manager.unmanage(self, force)

    def reset_state(self, state):
        """Update the share server with the provided state."""
        self.manager.reset_state(self, state)

    def migration_check(self, host, writable, nondisruptive,
                        preserve_snapshots, new_share_network_id=None):
        """Check if the new host is suitable for migration."""
        return self.manager.migration_check(
            self, host, writable, nondisruptive,
            preserve_snapshots, new_share_network_id=new_share_network_id)

    def migration_start(self, host, writable, nondisruptive,
                        preserve_snapshots, new_share_network_id=None):
        """Migrate the share server to a new host."""
        self.manager.migration_start(
            self, host, writable, nondisruptive,
            preserve_snapshots, new_share_network_id=new_share_network_id)

    def migration_complete(self):
        """Complete migration of a share server."""
        return self.manager.migration_complete(self)

    def migration_cancel(self):
        """Attempts to cancel migration of a share server."""
        self.manager.migration_cancel(self)

    def migration_get_progress(self):
        """Obtain progress of migration of a share server."""
        return self.manager.migration_get_progress(self)

    def reset_task_state(self, task_state):
        """Reset the task state of a given share server."""
        self.manager.reset_task_state(self, task_state)


class ShareServerManager(base.ManagerWithFind):
    """Manage :class:`ShareServer` resources."""
    resource_class = ShareServer

    def get(self, server):
        """Get a share server.

        :param server: ID of the :class:`ShareServer` to get.
        :rtype: :class:`ShareServer`
        """
        server_id = base.getid(server)
        server = self._get("%s/%s" % (RESOURCES_PATH, server_id),
                           RESOURCE_NAME)
        # Split big dict 'backend_details' to separated strings
        # as next:
        # +---------------------+------------------------------------+
        # |       Property      |                Value               |
        # +---------------------+------------------------------------+
        # | details:instance_id |35203a78-c733-4b1f-b82c-faded312e537|
        # +---------------------+------------------------------------+
        for k, v in server._info["backend_details"].items():
            server._info["details:%s" % k] = v
        return server

    def details(self, server):
        """Get a share server details.

        :param server: ID of the :class:`ShareServer` to get details from.
        :rtype: list of :class:`ShareServerBackendDetails
        """
        server_id = base.getid(server)
        return self._get("%s/%s/details" % (RESOURCES_PATH, server_id),
                         "details")

    def delete(self, server):
        """Delete share server.

        :param server: ID of the :class:`ShareServer` to delete.
        """
        server_id = base.getid(server)
        self._delete(RESOURCE_PATH % server_id)

    def list(self, search_opts=None):
        """Get a list of share servers.

        :rtype: list of :class:`ShareServer`
        """
        query_string = self._build_query_string(search_opts)
        return self._list(RESOURCES_PATH + query_string, RESOURCES_NAME)

    @api_versions.wraps("2.49", "2.50")
    def manage(self, host, share_network_id, identifier, driver_options=None):

        driver_options = driver_options or {}
        body = {
            'host': host,
            'share_network_id': share_network_id,
            'identifier': identifier,
            'driver_options': driver_options,
        }

        resource_path = RESOURCE_PATH % 'manage'
        return self._create(resource_path, {'share_server': body},
                            'share_server')

    @api_versions.wraps("2.51")  # noqa
    def manage(self, host, share_network_id, identifier,  # noqa
               share_network_subnet_id=None, driver_options=None):

        driver_options = driver_options or {}
        body = {
            'host': host,
            'share_network_id': share_network_id,
            'identifier': identifier,
            'share_network_subnet_id': share_network_subnet_id,
            'driver_options': driver_options,
        }

        resource_path = RESOURCE_PATH % 'manage'
        return self._create(resource_path, {'share_server': body},
                            'share_server')

    @api_versions.wraps("2.49")
    def unmanage(self, share_server, force=False):
        return self._action("unmanage", share_server, {'force': force})

    @api_versions.wraps("2.49")
    def reset_state(self, share_server, state):
        """Update the provided share server with the provided state.

        :param share_server: either share_server object or text with its ID.
        :param state: text with new state to set for share.
        """
        return self._action("reset_status", share_server, {"status": state})

    def _action(self, action, share_server, info=None):
        """Perform a share server 'action'.

        :param action: text with action name.
        :param share_server: either share_server object or text with its ID.
        :param info: dict with data for specified 'action'.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body)
        url = ACTION_PATH % base.getid(share_server)
        return self.api.client.post(url, body=body)

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def migration_check(self, share_server, host, writable, nondisruptive,
                        preserve_snapshots, new_share_network_id=None):
        """Check the share server migration to a new host

        :param share_server: either share_server object or text with its ID.
        :param host: Destination host where share server will be migrated.
        :param writable: Enforces migration to keep the shares writable.
        :param nondisruptive: Enforces migration to be nondisruptive.
        :param preserve_snapshots: Enforces migration to preserve snapshots.
        :param new_share_network_id: Specify the new share network id.
        """
        result = self._action(
            "migration_check", share_server, {
                "host": host,
                "preserve_snapshots": preserve_snapshots,
                "writable": writable,
                "nondisruptive": nondisruptive,
                "new_share_network_id": new_share_network_id,
            })
        return result[1]

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def migration_start(self, share_server, host, writable,
                        nondisruptive, preserve_snapshots,
                        new_share_network_id=None):
        """Migrates share server to a new host

        :param share_server: either share_server object or text with its ID.
        :param host: Destination host where share server will be migrated.
        :param writable: Enforces migration to keep the shares writable.
        :param nondisruptive: Enforces migration to be nondisruptive.
        :param preserve_snapshots: Enforces migration to preserve snapshots.
        :param new_share_network_id: Specify the new share network id.
        """
        return self._action(
            "migration_start", share_server, {
                "host": host,
                "writable": writable,
                "nondisruptive": nondisruptive,
                "preserve_snapshots": preserve_snapshots,
                "new_share_network_id": new_share_network_id,
            })

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def reset_task_state(self, share_server, task_state):
        """Update the provided share server with the provided task state.

        :param share_server: either share_server object or text with its ID.
        :param task_state: text with new task state to set for share.
        """
        return self._action('reset_task_state', share_server,
                            {"task_state": task_state})

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def migration_complete(self, share_server):
        """Completes migration for a given share server.

        :param share_server: either share_server object or text with its ID.
        """
        result = self._action('migration_complete', share_server)
        # NOTE(dviroel): result[0] is response code, result[1] is dict body
        return result[1]

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def migration_cancel(self, share_server):
        """Attempts to cancel migration for a given share server.

        :param share_server: either share_server object or text with its ID.
        """
        return self._action('migration_cancel',
                            share_server)

    @api_versions.wraps("2.57")
    @api_versions.experimental_api
    def migration_get_progress(self, share_server):
        """Obtains progress of share migration for a given share server.

        :param share_server: either share_server object or text with its ID.
        """
        result = self._action('migration_get_progress', share_server)
        # NOTE(felipefutty): result[0] is response code, result[1] is dict body
        return result[1]
