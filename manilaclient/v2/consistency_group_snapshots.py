# Copyright 2015 Chuck Fouts
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
"""Interface for consistency group snapshots extension."""

from six.moves.urllib import parse

from manilaclient import api_versions
from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base

RESOURCES_PATH = '/cgsnapshots'
RESOURCE_PATH = '/cgsnapshots/%s'
RESOURCE_PATH_ACTION = '/cgsnapshots/%s/action'
RESOURCES_NAME = 'cgsnapshots'
RESOURCE_NAME = 'cgsnapshot'
MEMBERS_RESOURCE_NAME = 'cgsnapshot_members'


class ConsistencyGroupSnapshot(common_base.Resource):
    """A group of snapshots taken of multiple shares."""

    def __repr__(self):
        return "<Consistency Group Snapshot: %s>" % self.id

    def update(self, **kwargs):
        """Update this consistency group snapshot."""
        self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this consistency group snapshot."""
        self.manager.delete(self)

    def reset_state(self, state):
        """Update the consistency group snapshot with the provided state."""
        self.manager.reset_state(self, state)


class ConsistencyGroupSnapshotManager(base.ManagerWithFind):
    resource_class = ConsistencyGroupSnapshot

    @api_versions.wraps("2.4")
    @api_versions.experimental_api
    def create(self, consistency_group_id, name=None, description=None):
        """Create a consistency group snapshot.

        :param name: text - name of the new cg snapshot
        :param description: text - description of the cg snapshot
        :rtype: :class:`ConsistencyGroup`
        """
        body = {
            'consistency_group_id': consistency_group_id,
            'name': name,
            'description': description,
        }
        return self._create(RESOURCES_PATH,
                            {RESOURCE_NAME: body},
                            RESOURCE_NAME)

    @api_versions.wraps("2.4")
    @api_versions.experimental_api
    def get(self, cg_snapshot):
        """Get a consistency group snapshot.

        :param cg_snapshot: either cg snapshot object or text with
            its ID.
        :rtype: :class:`ConsistencyGroup`
        """
        consistency_group_id = common_base.getid(cg_snapshot)
        return self._get(RESOURCE_PATH % consistency_group_id,
                         RESOURCE_NAME)

    @api_versions.wraps("2.4")
    @api_versions.experimental_api
    def update(self, cg_snapshot, **kwargs):
        """Updates a consistency group snapshot.

        :param cg_snapshot: either consistency group snapshot object or text
            with its ID.
        :rtype: :class:`ConsistencyGroup`
        """
        if not kwargs:
            return

        body = {RESOURCE_NAME: kwargs}
        cg_snapshot_id = common_base.getid(cg_snapshot)
        return self._update(RESOURCE_PATH % cg_snapshot_id,
                            body,
                            RESOURCE_NAME)

    @api_versions.wraps("2.4")
    @api_versions.experimental_api
    def list(self, detailed=True, search_opts=None):
        """Get a list of all consistency group snapshots.

        :param detailed: Whether to return detailed snapshot info or not.
        :param search_opts: dict with search options to filter out snapshots.
            available keys are below (('name1', 'name2', ...), 'type'):
            - ('all_tenants', int)
            - ('offset', int)
            - ('limit', int)
            Note, that member context will have restricted set of
            available search options.
        :rtype: list of :class:`ConsistencyGroupSnapshot`
        """

        if search_opts is None:
            search_opts = {}

        query_string = self._query_string_helper(search_opts)

        if detailed:
            path = RESOURCES_PATH + '/detail%s' % (query_string,)
        else:
            path = RESOURCES_PATH + '%s' % (query_string,)

        return self._list(path, RESOURCES_NAME)

    def _do_delete(self, cg_snapshot, force=False, action_name='force_delete'):
        """Delete a consistency group snapshot.

        :param cg_snapshot: either a cg snapshot object or text wit its ID.
        """
        cg_id = common_base.getid(cg_snapshot)
        body = None

        if force:
            body = {action_name: None}

        if body:
            self.api.client.post(RESOURCE_PATH_ACTION % cg_id, body=body)
        else:
            self._delete(RESOURCE_PATH % cg_id)

    @api_versions.wraps("2.4", "2.6")
    @api_versions.experimental_api
    def delete(self, cg_snapshot, force=False):
        return self._do_delete(cg_snapshot, force, 'os-force_delete')

    @api_versions.wraps("2.7")  # noqa
    @api_versions.experimental_api
    def delete(self, cg_snapshot, force=False):
        return self._do_delete(cg_snapshot, force, 'force_delete')

    @api_versions.wraps("2.4")
    @api_versions.experimental_api
    def members(self, cg_snapshot, search_opts=None):
        """Get a list of consistency group snapshot members.

        :param search_opts: dict with search options to filter out members.
            - ('offset', int)
            - ('limit', int)
        :rtype: list of :class:`ConsistencyGroupSnapshot`
        """

        consistency_group_id = common_base.getid(cg_snapshot)

        if search_opts is None:
            search_opts = {}

        query_string = self._query_string_helper(search_opts)
        path = RESOURCES_PATH + '/%s/members%s' % (consistency_group_id,
                                                   query_string,)

        return self._list(path, MEMBERS_RESOURCE_NAME)

    def _do_reset_state(self, cg_snapshot, state, action_name):
        """Update the specified consistency group with the provided state."""
        body = {action_name: {'status': state}}
        cg_id = common_base.getid(cg_snapshot)
        url = RESOURCE_PATH_ACTION % cg_id
        return self.api.client.post(url, body=body)

    @api_versions.wraps("2.4", "2.6")
    @api_versions.experimental_api
    def reset_state(self, cg_snapshot, state):
        return self._do_reset_state(cg_snapshot, state, 'os-reset_status')

    @api_versions.wraps("2.7")  # noqa
    @api_versions.experimental_api
    def reset_state(self, cg_snapshot, state):
        return self._do_reset_state(cg_snapshot, state, 'reset_status')

    def _query_string_helper(self, search_opts):
        q_string = parse.urlencode(
            sorted([(k, v) for (k, v) in list(search_opts.items()) if v]))
        if q_string:
            q_string = "?%s" % (q_string,)
        else:
            q_string = ''
        return q_string
