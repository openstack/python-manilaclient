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
from manilaclient import utils

RESOURCES_PATH = '/security-services'
RESOURCE_PATH = "/security-services/%s"
RESOURCE_NAME = 'security_service'
RESOURCES_NAME = 'security_services'


class SecurityService(base.Resource):
    """Security service for Manila shares """
    def __repr__(self):
        return "<SecurityService: %s>" % self.id


class SecurityServiceManager(base.Manager):
    """Manage :class:`SecurityService` resources."""
    resource_class = SecurityService

    def create(self, type, dns_ip=None, server=None, domain=None, sid=None,
               password=None, name=None, description=None):
        """Create security service for NAS.

        :param type: security service type - 'ldap', 'kerberos' or
                     'active_directory'
        :param dns_ip: dns ip address used inside tenant's network
        :param server: security service server ip address or hostname
        :param domain: security service domain
        :param sid: security identifier used by tenant
        :param password: password used by sid
        :param name: security service name
        :param description: security service description
        :rtype: :class:`SecurityService`
        """
        values = {'type': type}
        if dns_ip:
            values['dns_ip'] = dns_ip
        if server:
            values['server'] = server
        if domain:
            values['domain'] = domain
        if sid:
            values['sid'] = sid
        if password:
            values['password'] = password
        if name:
            values['name'] = name
        if description:
            values['description'] = description

        body = {RESOURCE_NAME: values}

        return self._create(RESOURCES_PATH, body, RESOURCE_NAME)

    def get(self, security_service):
        """Get a security service info.

        :param security_service: security service to get.
        :rtype: :class:`SecurityService`
        """
        return self._get(RESOURCE_PATH % security_service, RESOURCE_NAME)

    def update(self, security_service, dns_ip=None, server=None, domain=None,
               password=None, sid=None, name=None, description=None):
        """Updates a security service.

        :param security_service: security service to update.
        :param dns_ip: dns ip address used inside tenant's network
        :param server: security service server ip address or hostname
        :param domain: security service domain
        :param sid: security identifier used by tenant
        :param password: password used by sid
        :param name: security service name
        :param description: security service description
        :rtype: :class:`SecurityService`
        """

        values = {}
        if dns_ip:
            values['dns_ip'] = dns_ip
        if server:
            values['server'] = server
        if domain:
            values['domain'] = domain
        if sid:
            values['sid'] = sid
        if password:
            values['password'] = password
        if name:
            values['name'] = name
        if description:
            values['description'] = description

        if not values:
            msg = "Must specify fields to be updated"
            raise exceptions.CommandError(msg)

        body = {RESOURCE_NAME: values}

        return self._update(RESOURCE_PATH % security_service,
                            body,
                            RESOURCE_NAME)

    def delete(self, security_service):
        """Delete a security service.

        :param security_service: security service to be deleted.
        """
        self._delete(RESOURCE_PATH % security_service)

    def list(self, detailed=False, search_opts=None):
        """Get a list of all security services.

        :rtype: list of :class:`SecurityService`
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
