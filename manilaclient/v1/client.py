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

import warnings

from keystoneclient import adapter
from keystoneclient.v2_0 import client as keystone_client_v2
from keystoneclient.v3 import client as keystone_client_v3
import six

from manilaclient import exceptions
from manilaclient import httpclient
from manilaclient.v1 import limits
from manilaclient.v1 import quota_classes
from manilaclient.v1 import quotas
from manilaclient.v1 import scheduler_stats
from manilaclient.v1 import security_services
from manilaclient.v1 import services
from manilaclient.v1 import share_networks
from manilaclient.v1 import share_servers
from manilaclient.v1 import share_snapshots
from manilaclient.v1 import share_type_access
from manilaclient.v1 import share_types
from manilaclient.v1 import shares


class Client(object):
    """Top-level object to access the OpenStack Manila API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Or, alternatively, you can create a client instance using the
    keystoneclient.session API::

        >>> from keystoneclient.auth.identity import v2
        >>> from keystoneclient import session
        >>> from manilaclient import client
        >>> auth = v2.Password(auth_url=AUTH_URL,
                               username=USERNAME,
                               password=PASSWORD,
                               tenant_name=PROJECT_ID)
        >>> sess = session.Session(auth=auth)
        >>> manila = client.Client(VERSION, session=sess)

    Then call methods on its managers::

        >>> client.shares.list()
        ...
    """
    def __init__(self, username=None, api_key=None, project_id=None,
                 auth_url=None, insecure=False, timeout=None, tenant_id=None,
                 project_name=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='share', service_name=None, retries=None,
                 http_log_debug=False, input_auth_token=None, session=None,
                 auth=None, cacert=None, service_catalog_url=None,
                 user_agent='python-manilaclient',
                 use_keyring=False, force_new_token=False,
                 cached_token_lifetime=300, **kwargs):
        service_name = kwargs.get("share_service_name", service_name)

        def check_deprecated_arguments():
            deprecated = {
                'share_service_name': 'service_name',
                'proxy_tenant_id': None,
                'proxy_token': None,
                'os_cache': 'use_keyring'
            }

            for arg, replacement in six.iteritems(deprecated):
                if kwargs.get(arg, None) is None:
                    continue

                replacement_msg = ""

                if replacement is not None:
                    replacement_msg = " Use %s instead." % replacement

                msg = "Argument %(arg)s is deprecated.%(repl)s" % {
                    'arg': arg,
                    'repl': replacement_msg
                }
                warnings.warn(msg)

        check_deprecated_arguments()

        if input_auth_token and not service_catalog_url:
            msg = ("For token-based authentication you should "
                   "provide 'input_auth_token' and 'service_catalog_url'.")
            raise exceptions.ClientException(msg)

        self.project_id = tenant_id if tenant_id is not None else project_id
        self.keystone_client = None
        self.session = session

        # NOTE(u_glide): token authorization has highest priority.
        # That's why session and/or password will be ignored
        # if token is provided.
        if not input_auth_token:
            if session:
                self.keystone_client = adapter.LegacyJsonAdapter(
                    session=session,
                    auth=auth,
                    interface=endpoint_type,
                    service_type=service_type,
                    service_name=service_name,
                    region_name=region_name)
                input_auth_token = self.keystone_client.session.get_token(auth)

            else:
                self.keystone_client = self._get_keystone_client(
                    username=username,
                    api_key=api_key,
                    auth_url=auth_url,
                    project_id=self.project_id,
                    project_name=project_name,
                    use_keyring=use_keyring,
                    force_new_token=force_new_token,
                    stale_duration=cached_token_lifetime)
                input_auth_token = self.keystone_client.auth_token

        if not input_auth_token:
            raise RuntimeError("Not Authorized")

        if session and not service_catalog_url:
            service_catalog_url = self.keystone_client.session.get_endpoint(
                auth, interface=endpoint_type,
                service_type=service_type)
        elif not service_catalog_url:
            catalog = self.keystone_client.service_catalog.get_endpoints(
                service_type)

            if service_type in catalog:
                for e_type, endpoint in catalog.get(service_type)[0].items():
                    if str(e_type).lower() == str(endpoint_type).lower():
                        service_catalog_url = endpoint
                        break

        if not service_catalog_url:
            raise RuntimeError("Could not find Manila endpoint in catalog")

        self.client = httpclient.HTTPClient(service_catalog_url,
                                            input_auth_token,
                                            user_agent,
                                            insecure=insecure,
                                            cacert=cacert,
                                            timeout=timeout,
                                            retries=retries,
                                            http_log_debug=http_log_debug)

        self.limits = limits.LimitsManager(self)
        self.services = services.ServiceManager(self)
        self.security_services = security_services.SecurityServiceManager(self)
        self.share_networks = share_networks.ShareNetworkManager(self)

        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)

        self.shares = shares.ShareManager(self)
        self.share_snapshots = share_snapshots.ShareSnapshotManager(self)

        self.share_types = share_types.ShareTypeManager(self)
        self.share_type_access = share_type_access.ShareTypeAccessManager(self)
        self.share_servers = share_servers.ShareServerManager(self)
        self.pools = scheduler_stats.PoolManager(self)

        self._load_extensions(extensions)

    def _load_extensions(self, extensions):
        if not extensions:
            return

        for extension in extensions:
            if extension.manager_class:
                setattr(self, extension.name, extension.manager_class(self))

    def _get_keystone_client(self, username=None, api_key=None, auth_url=None,
                             token=None, project_id=None, project_name=None,
                             use_keyring=False, force_new_token=False,
                             stale_duration=0):
        if not auth_url:
            raise RuntimeError("No auth url specified")

        if not getattr(self, "keystone_client", None):
            imported_client = (keystone_client_v2 if "v2.0" in auth_url
                               else keystone_client_v3)

            self.keystone_client = imported_client.Client(
                username=username,
                password=api_key,
                token=token,
                tenant_id=project_id,
                tenant_name=project_name,
                auth_url=auth_url,
                endpoint=auth_url,
                use_keyring=use_keyring,
                force_new_token=force_new_token,
                stale_duration=stale_duration)

        self.keystone_client.authenticate()

        return self.keystone_client

    def authenticate(self):
        """Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        warnings.warn("authenticate() method is deprecated. "
                      "Client automatically makes authentication call "
                      "in the constructor.")
