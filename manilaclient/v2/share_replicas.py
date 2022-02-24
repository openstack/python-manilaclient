# Copyright 2015 Chuck Fouts.
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

RESOURCES_PATH = '/share-replicas'
RESOURCE_PATH = '/share-replicas/%s'
RESOURCE_PATH_ACTION = '/share-replicas/%s/action'
RESOURCES_NAME = 'share_replicas'
RESOURCE_NAME = 'share_replica'


class ShareReplica(base.Resource):
    """A replica is 'mirror' instance of a share at some point in time."""
    def __repr__(self):
        return "<Share Replica: %s>" % self.id

    def resync(self):
        """Re-sync this replica."""
        self.manager.resync(self)

    def promote(self):
        """Promote this replica to be the 'active' replica."""
        self.manager.promote(self)

    def reset_state(self, state):
        """Update replica's 'status' attr with the provided state."""
        self.manager.reset_state(self, state)

    def reset_replica_state(self, replica_state):
        """Update replica's 'replica_state' attr with the provided state."""
        self.manager.reset_replica_state(self, replica_state)


class ShareReplicaManager(base.ManagerWithFind):
    """Manage :class:`ShareReplica` resources."""
    resource_class = ShareReplica

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def get(self, replica):
        return self._get_share_replica(replica)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def get(self, replica):  # noqa F811
        return self._get_share_replica(replica)

    def _get_share_replica(self, replica):
        """Get a share replica.

        :param replica: either replica object or its UUID.
        :rtype: :class:`ShareReplica`
        """
        replica_id = base.getid(replica)
        return self._get(RESOURCE_PATH % replica_id, RESOURCE_NAME)

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def list(self, share=None, search_opts=None):
        return self._list_share_replicas(share=share, search_opts=search_opts)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def list(self, share=None, search_opts=None):  # noqa F811
        return self._list_share_replicas(share=share, search_opts=search_opts)

    def _list_share_replicas(self, share=None, search_opts=None):
        """List all share replicas or list replicas belonging to a share.

        :param share: either share object or its UUID.
        :param search_opts: default None
        :rtype: list of :class:`ShareReplica`
        """

        if share:
            share_id = '?share_id=' + base.getid(share)
            url = RESOURCES_PATH + '/detail' + share_id
            return self._list(url, RESOURCES_NAME)
        else:
            return self._list(RESOURCES_PATH + '/detail', RESOURCES_NAME)

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def promote(self, replica):
        """Promote the provided replica.

        :param replica: either replica object or its UUID.
        """
        return self._action('promote', replica)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def promote(self, replica):  # noqa F811
        """Promote the provided replica.

        :param replica: either replica object or its UUID.
        """
        return self._action('promote', replica)

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def create(self, share, availability_zone=None):
        return self._create_share_replica(
            share, availability_zone=availability_zone)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION, '2.66')  # noqa
    def create(self, share, availability_zone=None):  # noqa F811
        return self._create_share_replica(
            share, availability_zone=availability_zone)

    @api_versions.wraps("2.67")  # noqa
    def create(self, share, availability_zone=None, scheduler_hints=None): # noqa F811
        return self._create_share_replica(
            share, availability_zone=availability_zone,
            scheduler_hints=scheduler_hints)

    def _create_share_replica(self, share, availability_zone=None,
                              scheduler_hints=None):
        """Create a replica for a share.

        :param share: The share to create the replica of. Can be the share
        object or its UUID.
        :param availability_zone: The 'availability_zone' object or its UUID.
        :param scheduler_hints: The scheduler_hints as key=value pair. Only
        supported key is 'only_host'.
        """

        share_id = base.getid(share)
        body = {'share_id': share_id}

        if availability_zone:
            body['availability_zone'] = base.getid(availability_zone)

        if scheduler_hints:
            body['scheduler_hints'] = scheduler_hints
        return self._create(RESOURCES_PATH,
                            {RESOURCE_NAME: body},
                            RESOURCE_NAME)

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def delete(self, replica, force=False):
        """Delete a replica.

        :param replica: either replica object or its UUID.
        :param force: optional 'force' flag.
        """
        self._do_delete(replica, force=force)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def delete(self, replica, force=False):  # noqa F811
        """Delete a replica.

        :param replica: either replica object or its UUID.
        :param force: optional 'force' flag.
        """
        self._do_delete(replica, force=force)

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def reset_state(self, replica, state):
        """Reset the 'status' attr of the replica.

        :param replica: either replica object or its UUID.
        :param state: state to set the replica's 'status' attr to.
        """
        return self._do_reset_state(replica, state, "reset_status")

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def reset_state(self, replica, state):  # noqa F811
        """Reset the 'status' attr of the replica.

        :param replica: either replica object or its UUID.
        :param state: state to set the replica's 'status' attr to.
        """
        return self._do_reset_state(replica, state, "reset_status")

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def reset_replica_state(self, replica, state):
        """Reset the 'replica_state' attr of the replica.

        :param replica: either replica object or its UUID.
        :param state: state to set the replica's 'replica_state' attr to.
        """
        return self._do_reset_state(replica, state, "reset_replica_state")

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def reset_replica_state(self, replica, state):  # noqa F811
        """Reset the 'replica_state' attr of the replica.

        :param replica: either replica object or its UUID.
        :param state: state to set the replica's 'replica_state' attr to.
        """
        return self._do_reset_state(replica, state, "reset_replica_state")

    @api_versions.wraps("2.11", constants.REPLICA_PRE_GRADUATION_VERSION)
    @api_versions.experimental_api
    def resync(self, replica):
        """Re-sync the provided replica.

        :param replica: either replica object or its UUID.
        """
        return self._action('resync', replica)

    @api_versions.wraps(constants.REPLICA_GRADUATION_VERSION)  # noqa
    def resync(self, replica):  # noqa F811
        """Re-sync the provided replica.

        :param replica: either replica object or its UUID.
        """
        return self._action('resync', replica)

    def _action(self, action, replica, info=None, **kwargs):
        """Perform a share replica 'action'.

        :param action: text with action name.
        :param replica: either replica object or its UUID.
        :param info: dict with data for specified 'action'.
        :param kwargs: dict with data to be provided for action hooks.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        replica_id = base.getid(replica)
        url = RESOURCE_PATH_ACTION % replica_id
        return self.api.client.post(url, body=body)

    def _do_delete(self, replica, force=False):
        """Delete a share replica.

        :param replica: either share replica object or its UUID.
        """
        replica_id = base.getid(replica)
        url = RESOURCE_PATH % replica_id

        if force:
            self._do_force_delete(replica_id)
        else:
            self._delete(url)

    def _do_force_delete(self, replica, action_name="force_delete"):
        """Delete a share replica forcibly - share status will be avoided.

        :param replica: either share replica object or its UUID.
        """
        return self._action(action_name, base.getid(replica))

    def _do_reset_state(self, replica, state, action_name):
        """Update the provided share replica with the provided state.

        :param replica: either share replica object or its UUID.
        :param state: text with new state to set for share.
        """
        attr = action_name.split("reset_")[1]
        return self._action(action_name, replica, {attr: state})
