# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from manilaclient import client as httpclient
from manilaclient.v1 import limits
from manilaclient.v1 import quota_classes
from manilaclient.v1 import quotas
from manilaclient.v1 import security_services
from manilaclient.v1 import services
from manilaclient.v1 import share_networks
from manilaclient.v1 import share_servers
from manilaclient.v1 import share_snapshots
from manilaclient.v1 import shares
from manilaclient.v1 import volume_types


class Client(object):
    """Top-level object to access the OpenStack Manila API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> client.share.list()
        ...
    """

    def __init__(self, username, api_key, project_id=None, auth_url='',
                 insecure=False, timeout=None, tenant_id=None,
                 proxy_tenant_id=None, proxy_token=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='share', service_name=None,
                 share_service_name=None, retries=None,
                 http_log_debug=False,
                 cacert=None, os_cache=False):
        # FIXME(comstud): Rename the api_key argument above when we
        # know it's not being used as keyword argument
        password = api_key
        self.limits = limits.LimitsManager(self)
        self.services = services.ServiceManager(self)
        self.security_services = security_services.SecurityServiceManager(self)
        self.share_networks = share_networks.ShareNetworkManager(self)

        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)

        self.shares = shares.ShareManager(self)
        self.share_snapshots = share_snapshots.ShareSnapshotManager(self)

        self.volume_types = volume_types.VolumeTypeManager(self)
        self.share_servers = share_servers.ShareServerManager(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = httpclient.HTTPClient(
            username,
            password,
            project_id,
            auth_url,
            insecure=insecure,
            timeout=timeout,
            tenant_id=tenant_id,
            proxy_token=proxy_token,
            proxy_tenant_id=proxy_tenant_id,
            region_name=region_name,
            endpoint_type=endpoint_type,
            service_type=service_type,
            service_name=service_name,
            share_service_name=share_service_name,
            retries=retries,
            http_log_debug=http_log_debug,
            cacert=cacert,
            os_cache=os_cache)

    def authenticate(self):
        """Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
