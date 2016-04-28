# Copyright 2014 Mirantis Inc.
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

import traceback

from oslo_log import log
from tempest.lib.cli import base
from tempest.lib import exceptions as lib_exc

from manilaclient import config
from manilaclient.tests.functional import client
from manilaclient.tests.functional import utils

CONF = config.CONF
LOG = log.getLogger(__name__)


class handle_cleanup_exceptions(object):
    """Handle exceptions raised with cleanup operations.

    Always suppress errors when lib_exc.NotFound or lib_exc.Forbidden
    are raised.
    Suppress all other exceptions only in case config opt
    'suppress_errors_in_cleanup' is True.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not (isinstance(exc_value,
                           (lib_exc.NotFound, lib_exc.Forbidden)) or
                CONF.suppress_errors_in_cleanup):
            return False  # Do not suppress error if any
        if exc_traceback:
            LOG.error("Suppressed cleanup error: "
                      "\n%s" % traceback.format_exc())
        return True  # Suppress error if any


class BaseTestCase(base.ClientTestBase):

    # Will be cleaned up after test suite run
    class_resources = []

    # Will be cleaned up after single test run
    method_resources = []

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.addCleanup(self.clear_resources)

    @classmethod
    def tearDownClass(cls):
        super(BaseTestCase, cls).tearDownClass()
        cls.clear_resources(cls.class_resources)

    @classmethod
    def clear_resources(cls, resources=None):
        """Deletes resources, that were created in test suites.

        This method tries to remove resources from resource list,
        if it is not found, assume it was deleted in test itself.
        It is expected, that all resources were added as LIFO
        due to restriction of deletion resources, that are in the chain.
        :param resources: dict with keys 'type','id','client' and 'deleted'
        """

        if resources is None:
            resources = cls.method_resources
        for res in resources:
            if "deleted" not in res:
                res["deleted"] = False
            if "client" not in res:
                res["client"] = cls.get_cleanup_client()
            if not(res["deleted"]):
                res_id = res["id"]
                client = res["client"]
                with handle_cleanup_exceptions():
                    # TODO(vponomaryov): add support for other resources
                    if res["type"] is "share_type":
                        client.delete_share_type(
                            res_id, microversion=res["microversion"])
                        client.wait_for_share_type_deletion(
                            res_id, microversion=res["microversion"])
                    elif res["type"] is "share_network":
                        client.delete_share_network(
                            res_id, microversion=res["microversion"])
                        client.wait_for_share_network_deletion(
                            res_id, microversion=res["microversion"])
                    elif res["type"] is "share":
                        client.delete_share(
                            res_id, microversion=res["microversion"])
                        client.wait_for_share_deletion(
                            res_id, microversion=res["microversion"])
                    else:
                        LOG.warning("Provided unsupported resource type for "
                                    "cleanup '%s'. Skipping." % res["type"])
                res["deleted"] = True

    @classmethod
    def get_admin_client(cls):
        manilaclient = client.ManilaCLIClient(
            username=CONF.admin_username,
            password=CONF.admin_password,
            tenant_name=CONF.admin_tenant_name,
            uri=CONF.admin_auth_url or CONF.auth_url,
            insecure=CONF.insecure,
            cli_dir=CONF.manila_exec_dir)
        # Set specific for admin project share network
        manilaclient.share_network = CONF.admin_share_network
        return manilaclient

    @classmethod
    def get_user_client(cls):
        manilaclient = client.ManilaCLIClient(
            username=CONF.username,
            password=CONF.password,
            tenant_name=CONF.tenant_name,
            uri=CONF.auth_url,
            insecure=CONF.insecure,
            cli_dir=CONF.manila_exec_dir)
        # Set specific for user project share network
        manilaclient.share_network = CONF.share_network
        return manilaclient

    @property
    def admin_client(self):
        if not hasattr(self, '_admin_client'):
            self._admin_client = self.get_admin_client()
        return self._admin_client

    @property
    def user_client(self):
        if not hasattr(self, '_user_client'):
            self._user_client = self.get_user_client()
        return self._user_client

    def _get_clients(self):
        return {'admin': self.admin_client, 'user': self.user_client}

    def skip_if_microversion_not_supported(self, microversion):
        if not utils.is_microversion_supported(microversion):
            raise self.skipException(
                "Microversion '%s' is not supported." % microversion)

    @classmethod
    def create_share_type(cls, name=None, driver_handles_share_servers=True,
                          snapshot_support=True, is_public=True, client=None,
                          cleanup_in_class=True, microversion=None):
        if client is None:
            client = cls.get_admin_client()
        share_type = client.create_share_type(
            name=name,
            driver_handles_share_servers=driver_handles_share_servers,
            snapshot_support=snapshot_support,
            is_public=is_public,
            microversion=microversion,
        )
        resource = {
            "type": "share_type",
            "id": share_type["ID"],
            "client": client,
            "microversion": microversion,
        }
        if cleanup_in_class:
            cls.class_resources.insert(0, resource)
        else:
            cls.method_resources.insert(0, resource)
        return share_type

    @classmethod
    def create_share_network(cls, name=None, description=None,
                             nova_net_id=None, neutron_net_id=None,
                             neutron_subnet_id=None, client=None,
                             cleanup_in_class=True, microversion=None):
        if client is None:
            client = cls.get_admin_client()
        share_network = client.create_share_network(
            name=name,
            description=description,
            nova_net_id=nova_net_id,
            neutron_net_id=neutron_net_id,
            neutron_subnet_id=neutron_subnet_id,
            microversion=microversion,
        )
        resource = {
            "type": "share_network",
            "id": share_network["id"],
            "client": client,
            "microversion": microversion,
        }
        if cleanup_in_class:
            cls.class_resources.insert(0, resource)
        else:
            cls.method_resources.insert(0, resource)
        return share_network

    @classmethod
    def create_share(cls, share_protocol=None, size=None, share_network=None,
                     share_type=None, name=None, description=None,
                     public=False, snapshot=None, metadata=None,
                     client=None, cleanup_in_class=False,
                     wait_for_creation=True, microversion=None):
        if client is None:
            client = cls.get_admin_client()
        data = {
            'share_protocol': share_protocol or client.share_protocol,
            'size': size or 1,
            'name': name,
            'description': description,
            'public': public,
            'snapshot': snapshot,
            'metadata': metadata,
            'microversion': microversion,
        }
        share_network = share_network or client.share_network
        share_type = share_type or CONF.share_type
        if share_network:
            data['share_network'] = share_network
        if share_type:
            data['share_type'] = share_type
        share = client.create_share(**data)
        resource = {
            "type": "share",
            "id": share["id"],
            "client": client,
            "microversion": microversion,
        }
        if cleanup_in_class:
            cls.class_resources.insert(0, resource)
        else:
            cls.method_resources.insert(0, resource)
        if wait_for_creation:
            client.wait_for_share_status(share['id'], 'available')
        return share

    @classmethod
    def create_security_service(cls, type='ldap', name=None, description=None,
                                dns_ip=None, server=None, domain=None,
                                user=None, password=None, client=None,
                                cleanup_in_class=False, microversion=None):
        if client is None:
            client = cls.get_admin_client()
        data = {
            'type': type,
            'name': name,
            'description': description,
            'user': user,
            'password': password,
            'server': server,
            'domain': domain,
            'dns_ip': dns_ip,
            'microversion': microversion,
        }
        ss = client.create_security_service(**data)
        resource = {
            "type": "share",
            "id": ss["id"],
            "client": client,
            "microversion": microversion,
        }
        if cleanup_in_class:
            cls.class_resources.insert(0, resource)
        else:
            cls.method_resources.insert(0, resource)
        return ss
