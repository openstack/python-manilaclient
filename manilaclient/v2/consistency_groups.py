# Copyright 2015 Andrew Kerr
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
"""Interface for consistency groups extension."""

from six.moves.urllib import parse

from manilaclient import api_versions
from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base

RESOURCES_PATH = '/consistency-groups'
RESOURCE_PATH = '/consistency-groups/%s'
RESOURCE_PATH_ACTION = '/consistency-groups/%s/action'
RESOURCES_NAME = 'consistency_groups'
RESOURCE_NAME = 'consistency_group'


class ConsistencyGroup(common_base.Resource):
    """A consistency group is a logical grouping of shares."""
    def __repr__(self):
        return "<Consistency Group: %s>" % self.id

    def update(self, **kwargs):
        """Update this consistency group."""
        self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this consistency group."""
        self.manager.delete(self)

    def reset_state(self, state):
        """Update the consistency group with the provided state."""
        self.manager.reset_state(self, state)


class ConsistencyGroupManager(base.ManagerWithFind):
    """Manage :class:`ConsistencyGroup` resources."""
    resource_class = ConsistencyGroup

    @api_versions.wraps("2.4")
    def create(self, share_network=None, name=None, description=None,
               source_cgsnapshot_id=None, share_types=None):
        """Create a Consistency Group.

        :param share_network: either the share network object or text of the
            uuid - represents the share network to use when creating a
            consistency group with multi-svm capabilities.
        :param name: text - name of the new consistency group
        :param description: text - description of the consistency group
        :param source_cgsnapshot_id: text - The uuid of the cgsnapshot from
            which this CG was created. Cannot be supplied when 'share_types'
            is provided.
        :param share_types: List of the share types that shares in the CG are
            allowed to be a part of. Cannot be supplied when
            'source_cgsnapshot_id' is provided.
        :rtype: :class:`ConsistencyGroup`
        """
        if share_types:
            share_types = [common_base.getid(share_type)
                           for share_type in share_types]

        body = {'name': name, 'description': description}

        share_network_id = None
        if share_network:
            share_network_id = common_base.getid(share_network)
        if share_network_id:
            body['share_network_id'] = share_network_id
        if source_cgsnapshot_id:
            body['source_cgsnapshot_id'] = source_cgsnapshot_id
        if share_types:
            body['share_types'] = share_types
        return self._create(RESOURCES_PATH,
                            {RESOURCE_NAME: body}, RESOURCE_NAME)

    @api_versions.wraps("2.4")
    def get(self, consistency_group):
        """Get a consistency group.

        :param consistency_group: either consistency group object or text with
            its ID.
        :rtype: :class:`ConsistencyGroup`
        """
        consistency_group_id = common_base.getid(consistency_group)
        return self._get(RESOURCE_PATH % consistency_group_id,
                         RESOURCE_NAME)

    @api_versions.wraps("2.4")
    def update(self, consistency_group, **kwargs):
        """Updates a consistency group.

        :param consistency_group: either consistency group object or text
            with its ID.
        :rtype: :class:`ConsistencyGroup`
        """
        if not kwargs:
            return

        body = {RESOURCE_NAME: kwargs}
        consistency_group_id = common_base.getid(consistency_group)
        return self._update(RESOURCE_PATH % consistency_group_id,
                            body,
                            RESOURCE_NAME)

    @api_versions.wraps("2.4")
    def list(self, detailed=True, search_opts=None,
             sort_key=None, sort_dir=None):
        """Get a list of all shares.

        :param detailed: Whether to return detailed share info or not.
        :param search_opts: dict with search options to filter out shares.
            available keys are below (('name1', 'name2', ...), 'type'):
            - ('offset', int)
            - ('limit', int)
        :rtype: list of :class:`ConsistencyGroup`
        """
        if search_opts is None:
            search_opts = {}

        query_string = self._query_string_helper(search_opts)

        if detailed:
            path = RESOURCES_PATH + '/detail%s' % (query_string,)
        else:
            path = RESOURCES_PATH + '%s' % (query_string,)

        return self._list(path, RESOURCES_NAME)

    def _do_delete(self, consistency_group, force=False,
                   action_name='force_delete'):
        """Delete a consistency group.

        :param consistency_group: either consistency group object or text with
            its ID.
        """
        cg_id = common_base.getid(consistency_group)
        url = RESOURCE_PATH % cg_id
        body = None

        if force:
            body = {action_name: None}

        if body:
            self.api.client.post(url + '/action', body=body)
        else:
            self._delete(url)

    @api_versions.wraps("2.4", "2.6")
    def delete(self, consistency_group, force=False):
        return self._do_delete(consistency_group, force, 'os-force_delete')

    @api_versions.wraps("2.7")  # noqa
    def delete(self, consistency_group, force=False):
        return self._do_delete(consistency_group, force, 'force_delete')

    def _do_reset_state(self, consistency_group, state, action_name):
        """Update the specified consistency group with the provided state."""
        body = {action_name: {'status': state}}
        url = RESOURCE_PATH_ACTION % common_base.getid(consistency_group)
        return self.api.client.post(url, body=body)

    @api_versions.wraps("2.4", "2.6")
    def reset_state(self, cg, state):
        return self._do_reset_state(
            consistency_group, state, 'os-reset_status')

    @api_versions.wraps("2.7")  # noqa
    def reset_state(self, consistency_group, state):
        return self._do_reset_state(consistency_group, state, 'reset_status')

    def _query_string_helper(self, search_opts):
        q_string = parse.urlencode(
            sorted([(k, v) for (k, v) in list(search_opts.items()) if v]))
        if q_string:
            q_string = "?%s" % (q_string,)
        else:
            q_string = ''
        return q_string
