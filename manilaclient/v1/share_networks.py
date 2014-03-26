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
import urllib

from manilaclient import base
from manilaclient import exceptions

RESOURCES_PATH = '/share-networks'
RESOURCE_PATH = "/share-networks/%s"
RESOURCE_NAME = 'share_network'
RESOURCES_NAME = 'share_networks'


class ShareNetwork(base.Resource):
    """Network info for Manila shares """
    def __repr__(self):
        return "<ShareNetwork: %s>" % self.id


class ShareNetworkManager(base.Manager):
    """Manage :class:`ShareNetwork` resources."""
    resource_class = ShareNetwork

    def create(self, neutron_net_id=None, neutron_subnet_id=None,
               name=None, description=None):
        """Create share network.

        :param metadata: metadata specific to the manila network plugin in use
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

    def add_security_service(self, share_network, security_service):
        """Associate given security service with a share network

        :param share_network: share network name or id
        :param security_service: security service name or id
        :rtype: :class:`ShareNetwork`
        """
        body = {'add_security_service': {'security_service_id':
                                         security_service}}

        return self._create(RESOURCE_PATH % share_network + '/action',
                            body,
                            RESOURCE_NAME)

    def remove_security_service(self, share_network, security_service):
        """Dissociate security service from a share network

        :param share_network: share network name or id
        :param security_service: security service name or id
        :rtype: :class:`ShareNetwork`
        """
        body = {'remove_security_service': {'security_service_id':
                                            security_service}}

        return self._create(RESOURCE_PATH % share_network + '/action',
                            body,
                            RESOURCE_NAME)

    def activate(self, share_network):
        """Activate share network

        :param share_network: share network to be activated
        :rtype: :class:`ShareNetwork`
        """
        body = {'activate': {}}

        self._create(RESOURCE_PATH % share_network + '/action',
                     body,
                     RESOURCE_NAME)

    def deactivate(self, share_network):
        """Deactivate share network

        :param share_network: share network to be deactivated
        :rtype: :class:`ShareNetwork`
        """
        body = {'deactivate': {}}

        self._create(RESOURCE_PATH % share_network + '/action',
                     body,
                     RESOURCE_NAME)

    def get(self, share_network):
        """Get a share network.

        :param policy: share network to get.
        :rtype: :class:`NetworkInfo`
        """
        return self._get(RESOURCE_PATH % base.getid(share_network),
                         RESOURCE_NAME)

    def update(self, share_network, neutron_net_id=None,
               neutron_subnet_id=None, name=None, description=None):
        """Updates a share network.

        :param share_network: share network to update.
        :rtype: :class:`NetworkInfo`
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

        if not values:
            msg = "Must specify fields to be updated"
            raise exceptions.CommandError(msg)

        body = {RESOURCE_NAME: values}

        return self._update(RESOURCE_PATH % share_network,
                            body,
                            RESOURCE_NAME)

    def delete(self, share_network):
        """Delete a share network.

        :param share_network: share network to be deleted.
        """
        self._delete(RESOURCE_PATH % share_network)

    def list(self, detailed=False, search_opts=None):
        """Get a list of all share network.

        :rtype: list of :class:`NetworkInfo`
        """
        if search_opts:
            query_string = urllib.urlencode([(key, value)
                                             for (key, value)
                                             in search_opts.items()
                                             if value])
            if query_string:
                query_string = "?%s" % query_string
        else:
            query_string = ''

        if detailed:
            path = RESOURCES_PATH + "/detail" + query_string
        else:
            path = RESOURCES_PATH + query_string

        return self._list(path, RESOURCES_NAME)
