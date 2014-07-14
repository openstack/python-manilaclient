# Copyright 2014 OpenStack LLC.
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

import six
try:
    from urllib import urlencode  # noqa
except ImportError:
    from urllib.parse import urlencode  # noqa

from manilaclient import base
from manilaclient.openstack.common.apiclient import base as common_base

RESOURCES_PATH = '/os-services'
RESOURCES_NAME = 'services'


class Service(common_base.Resource):

    def __repr__(self):
        return "<Service: %s>" % self.id


class ServiceManager(base.Manager):
    """Manage :class:`Service` resources."""
    resource_class = Service

    def list(self, search_opts=None):
        """Get a list of all services.

        :rtype: list of :class:`Service`
        """
        query_string = ''
        if search_opts:
            query_string = urlencode(
                sorted([(k, v) for (k, v) in six.iteritems(search_opts) if v]))
            if query_string:
                query_string = "?%s" % query_string
        return self._list(RESOURCES_PATH + query_string, RESOURCES_NAME)
