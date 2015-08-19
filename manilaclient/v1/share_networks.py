# Copyright 2013 OpenStack LLC.
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

try:
    from urllib import urlencode  # noqa
except ImportError:
    from urllib.parse import urlencode  # noqa

import six

from manilaclient import base
from manilaclient import exceptions
from manilaclient.openstack.common.apiclient import base as common_base

RESOURCES_PATH = '/share-networks'
RESOURCE_PATH = "/share-networks/%s"
RESOURCE_NAME = 'share_network'
RESOURCES_NAME = 'share_networks'


class ShareNetwork(common_base.Resource):
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

    def add_security_service(self, share_network, security_service):
        """Associate given security service with a share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param security_service: name, id or SecurityService instance
        :rtype: :class:`ShareNetwork`
        """
        body = {
            'add_security_service': {
                'security_service_id': common_base.getid(security_service),
            },
        }
        return self._create(
            RESOURCE_PATH % common_base.getid(share_network) + '/action',
            body,
            RESOURCE_NAME,
        )

    def remove_security_service(self, share_network, security_service):
        """Dissociate security service from a share network.

        :param share_network: share network name, id or ShareNetwork instance
        :param security_service: name, id or SecurityService instance
        :rtype: :class:`ShareNetwork`
        """
        body = {
            'remove_security_service': {
                'security_service_id': common_base.getid(security_service),
            },
        }
        return self._create(
            RESOURCE_PATH % common_base.getid(share_network) + '/action',
            body,
            RESOURCE_NAME,
        )

    def get(self, share_network):
        """Get a share network.

        :param policy: share network to get.
        :rtype: :class:`NetworkInfo`
        """
        return self._get(RESOURCE_PATH % common_base.getid(share_network),
                         RESOURCE_NAME)

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

        for k, v in six.iteritems(values):
            if v == '':
                values[k] = None

        if not values:
            msg = "Must specify fields to be updated"
            raise exceptions.CommandError(msg)

        body = {RESOURCE_NAME: values}
        return self._update(RESOURCE_PATH % common_base.getid(share_network),
                            body,
                            RESOURCE_NAME)

    def delete(self, share_network):
        """Delete a share network.

        :param share_network: share network to be deleted.
        """
        self._delete(RESOURCE_PATH % common_base.getid(share_network))

    def list(self, detailed=True, search_opts=None):
        """Get a list of all share network.

        :rtype: list of :class:`NetworkInfo`
        """
        if search_opts:
            query_string = urlencode(
                sorted([(k, v) for (k, v) in list(search_opts.items()) if v]))
            if query_string:
                query_string = "?%s" % query_string
        else:
            query_string = ''

        if detailed:
            path = RESOURCES_PATH + "/detail" + query_string
        else:
            path = RESOURCES_PATH + query_string

        return self._list(path, RESOURCES_NAME)
