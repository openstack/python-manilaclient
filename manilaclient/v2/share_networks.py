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
from manilaclient import exceptions

RESOURCES_PATH = '/share-networks'
RESOURCE_PATH = "/share-networks/%s"
RESOURCE_NAME = 'share_network'
RESOURCES_NAME = 'share_networks'
ACTION_PATH = RESOURCE_PATH + '/action'


class ShareNetwork(base.Resource):
    """Network info for Manila shares."""
    def __repr__(self):
        return "<ShareNetwork: %s>" % self.id

    def update(self, **kwargs):
        """Update this share network."""
        return self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this share network."""
        self.manager.delete(self)


class ShareNetworkManager(base.ManagerWithFind):
    """Manage :class:`ShareNetwork` resources."""
    resource_class = ShareNetwork

    @api_versions.wraps("1.0", "2.25")
    def create(self, neutron_net_id=None, neutron_subnet_id=None,
               nova_net_id=None, name=None, description=None):
        """Create share network.

        :param neutron_net_id: ID of Neutron network
        :param neutron_subnet_id: ID of Neutron subnet
        :param nova_net_id: ID of Nova network
        :param name: share network name
        :param description: share network description
        :rtype: :class:`ShareNetwork`
        """
        values = {}
        if neutron_net_id:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id:
            values['neutron_subnet_id'] = neutron_subnet_id
        if nova_net_id:
            values['nova_net_id'] = nova_net_id
        if name:
            values['name'] = name
        if description:
            values['description'] = description

        body = {RESOURCE_NAME: values}

        return self._create(RESOURCES_PATH, body, RESOURCE_NAME)

    @api_versions.wraps("2.26", "2.50")  # noqa
    def create(self, neutron_net_id=None, neutron_subnet_id=None,   # noqa
               name=None, description=None):
        """Create share network.

        :param neutron_net_id: ID of Neutron network
        :param neutron_subnet_id: ID of Neutron subnet
        :param name: share network name
        :param description: share network description
        :rtype: :class:`ShareNetwork`
        """
        values = {}
        if neutron_net_id:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id:
            values['neutron_subnet_id'] = neutron_subnet_id
        if name:
            values['name'] = name
        if description:
            values['description'] = description

        body = {RESOURCE_NAME: values}

        return self._create(RESOURCES_PATH, body, RESOURCE_NAME)

    @api_versions.wraps("2.51")  # noqa
    def create(self, neutron_net_id=None, neutron_subnet_id=None,   # noqa
               name=None, description=None, availability_zone=None):
        values = {}

        if neutron_net_id:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id:
            values['neutron_subnet_id'] = neutron_subnet_id
        if name:
            values['name'] = name
        if description:
            values['description'] = description
        if availability_zone:
            values['availability_zone'] = availability_zone

        body = {RESOURCE_NAME: values}

        return self._create(RESOURCES_PATH, body, RESOURCE_NAME)

    def remove_security_service(self, share_network, security_service):
        """Dissociate security service from a share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param security_service: name, id or SecurityService instance
        :rtype: :class:`ShareNetwork`
        """
        body = {
            'remove_security_service': {
                'security_service_id': base.getid(security_service),
            },
        }
        return self._create(
            RESOURCE_PATH % base.getid(share_network) + '/action',
            body,
            RESOURCE_NAME,
        )

    def get(self, share_network):
        """Get a share network.

        :param policy: share network to get.
        :rtype: :class:`NetworkInfo`
        """
        return self._get(RESOURCE_PATH % base.getid(share_network),
                         RESOURCE_NAME)

    @api_versions.wraps("1.0", "2.25")
    def update(self, share_network, neutron_net_id=None,
               neutron_subnet_id=None, nova_net_id=None,
               name=None, description=None):
        """Updates a share network.

        :param share_network: share network to update.
        :rtype: :class:`ShareNetwork`
        """
        values = {}
        if neutron_net_id is not None:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id is not None:
            values['neutron_subnet_id'] = neutron_subnet_id
        if nova_net_id is not None:
            values['nova_net_id'] = nova_net_id
        if name is not None:
            values['name'] = name
        if description is not None:
            values['description'] = description

        for k, v in values.items():
            if v == '':
                values[k] = None

        if not values:
            msg = "Must specify fields to be updated"
            raise exceptions.CommandError(msg)

        body = {RESOURCE_NAME: values}
        return self._update(RESOURCE_PATH % base.getid(share_network),
                            body,
                            RESOURCE_NAME)

    @api_versions.wraps("2.26")  # noqa
    def update(self, share_network, neutron_net_id=None,   # noqa
               neutron_subnet_id=None, name=None,
               description=None):
        """Updates a share network.

        :param share_network: share network to update.
        :rtype: :class:`ShareNetwork`
        """
        values = {}
        if neutron_net_id is not None:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id is not None:
            values['neutron_subnet_id'] = neutron_subnet_id
        if name is not None:
            values['name'] = name
        if description is not None:
            values['description'] = description

        for k, v in values.items():
            if v == '':
                values[k] = None

        if not values:
            msg = "Must specify fields to be updated"
            raise exceptions.CommandError(msg)

        body = {RESOURCE_NAME: values}
        return self._update(RESOURCE_PATH % base.getid(share_network),
                            body,
                            RESOURCE_NAME)

    def delete(self, share_network):
        """Delete a share network.

        :param share_network: share network to be deleted.
        """
        self._delete(RESOURCE_PATH % base.getid(share_network))

    def list(self, detailed=True, search_opts=None):
        """Get a list of all share network.

        :rtype: list of :class:`NetworkInfo`
        """
        query_string = self._build_query_string(search_opts)

        if detailed:
            path = RESOURCES_PATH + "/detail" + query_string
        else:
            path = RESOURCES_PATH + query_string

        return self._list(path, RESOURCES_NAME)

    def _action(self, action, share_network, info=None):
        """Perform a share network 'action'.

        :param action: text with action name.
        :param share_network: either share_network object or text with its ID.
        :param info: dict with data for specified 'action'.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body)
        url = ACTION_PATH % base.getid(share_network)
        return self.api.client.post(url, body=body)

    def add_security_service(self, share_network, security_service):
        """Associate given security service with a share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param security_service: name, id or SecurityService instance
        :rtype: :class:`ShareNetwork`
        """
        info = {
            'security_service_id': base.getid(security_service),
        }
        return self._action('add_security_service', share_network, info)

    @api_versions.wraps("2.63")
    def add_security_service_check(self, share_network, security_service,
                                   reset_operation=False):
        """Associate given security service with a share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param security_service: name, id or SecurityService instance
        :param reset_operation: start over the check operation
        :rtype: :class:`ShareNetwork`
        """
        info = {
            'security_service_id': base.getid(security_service),
            'reset_operation': reset_operation,
        }
        return self._action('add_security_service_check', share_network, info)

    @api_versions.wraps("2.63")
    def update_share_network_security_service(self, share_network,
                                              current_security_service,
                                              new_security_service):
        """Update current security service to new one of a given share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param current_security_service: current name, id or
        SecurityService instance that will be changed
        :param new_security_service: new name, id or
        SecurityService instance that will be updated
        :rtype: :class:`ShareNetwork`
        """
        info = {
            'current_service_id': base.getid(current_security_service),
            'new_service_id': base.getid(new_security_service)}

        return self._action('update_security_service', share_network, info)

    @api_versions.wraps("2.63")
    def update_share_network_security_service_check(
            self, share_network, current_security_service,
            new_security_service, reset_operation=False):
        """Validates if the security service update is supported by all hosts.

        :param share_network: share network name, id or ShareNetwork instance
        :param current_security_service: current name, id or
        SecurityService instance that will be changed
        :param new_security_service: new name, id or
        :param reset_operation: start over the check operation
        SecurityService instance that will be updated
        :rtype: :class:`ShareNetwork`
        """
        info = {
            'current_service_id': base.getid(current_security_service),
            'new_service_id': base.getid(new_security_service),
            'reset_operation': reset_operation
        }

        return self._action('update_security_service_check',
                            share_network, info)

    @api_versions.wraps("2.63")
    def reset_state(self, share_network, state):
        """Reset state of a share network.

        :param share_network: either share_network object or text with its ID
        or name.
        :param state: text with new state to set for share network.
        """
        return self._action('reset_status', share_network,
                            {"status": state})
