# Copyright 2014 OpenStack Foundation
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

"""Share type access interface."""

from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base


class ShareTypeAccess(common_base.Resource):
    def __repr__(self):
        return "<ShareTypeAccess: %s>" % self.id


class ShareTypeAccessManager(base.ManagerWithFind):
    """Manage :class:`ShareTypeAccess` resources."""

    resource_class = ShareTypeAccess

    def list(self, share_type):
        if share_type.is_public:
            return None

        return self._list(
            '/types/%s/os-share-type-access' % common_base.getid(share_type),
            'share_type_access')

    def add_project_access(self, share_type, project):
        """Add a project to the given share type access list."""
        info = {'project': project}
        self._action('addProjectAccess', share_type, info)

    def remove_project_access(self, share_type, project):
        """Remove a project from the given share type access list."""
        info = {'project': project}
        self._action('removeProjectAccess', share_type, info)

    def _action(self, action, share_type, info, **kwargs):
        """Perform a share type action."""
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/types/%s/action' % common_base.getid(share_type)
        return self.api.client.post(url, body=body)
