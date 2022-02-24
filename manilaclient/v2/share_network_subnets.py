# Copyright 2019 NetApp
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

from manilaclient import base

RESOURCES_PATH = '/share-networks/%(share_network_id)s/subnets'
RESOURCE_PATH = RESOURCES_PATH + '/%(share_network_subnet_id)s'
RESOURCE_NAME = 'share_network_subnet'


class ShareNetworkSubnet(base.Resource):
    """Network subnet info for Manila share networks."""
    def __repr__(self):
        return "<ShareNetworkSubnet: %s>" % self.id

    def __getitem__(self, key):
        return self._info[key]

    def delete(self):
        """Delete this share network subnet."""
        self.manager.delete(self)


class ShareNetworkSubnetManager(base.ManagerWithFind):
    """Manage :class:`ShareNetworkSubnet` resources."""

    resource_class = ShareNetworkSubnet

    def create(self, neutron_net_id=None, neutron_subnet_id=None,
               availability_zone=None, share_network_id=None):
        """Create share network subnet.

        :param neutron_net_id: ID of Neutron network
        :param neutron_subnet_id: ID of Neutron subnet
        :param availability_zone: Name of the target availability zone
        :rtype: :class:`ShareNetworkSubnet`
        """
        values = {}
        if neutron_net_id:
            values['neutron_net_id'] = neutron_net_id
        if neutron_subnet_id:
            values['neutron_subnet_id'] = neutron_subnet_id
        if availability_zone:
            values['availability_zone'] = availability_zone

        body = {'share-network-subnet': values}
        url = '/share-networks/%(share_network_id)s/subnets' % {
            'share_network_id': share_network_id
        }

        return self._create(url, body, RESOURCE_NAME)

    def get(self, share_network, share_network_subnet):
        """Get a share network subnet.

        :param policy: share network subnet to get.
        :rtype: :class:`NetworkSubnetInfo`
        """
        share_network_id = base.getid(share_network)
        share_network_subnet_id = base.getid(share_network_subnet)
        url = ('/share-networks/%(share_network_id)s/subnets'
               '/%(share_network_subnet)s') % {
            'share_network_id': share_network_id,
            'share_network_subnet': share_network_subnet_id
        }
        return self._get(url, "share_network_subnet")

    def delete(self, share_network, share_network_subnet):
        """Delete a share network subnet.

        :param share_network: share network that owns the subnet.
        :param share_network_subnet: share network subnet to be deleted.
        """
        url = ('/share-networks/%(share_network_id)s/subnets'
               '/%(share_network_subnet)s') % {
            'share_network_id': base.getid(share_network),
            'share_network_subnet': share_network_subnet
        }
        self._delete(url)
