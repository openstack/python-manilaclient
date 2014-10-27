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

import os

from tempest_lib.cli import base

from manilaclient import config
from manilaclient.tests.functional import client

CONF = config.CONF


class BaseTestCase(base.ClientTestBase):
    def _get_clients(self):
        cli_dir = os.environ.get(
            'OS_MANILA_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/functional/bin'))

        clients = {
            'admin': client.ManilaCLIClient(
                username=CONF.admin_username,
                password=CONF.admin_password,
                tenant_name=CONF.admin_tenant_name,
                uri=CONF.admin_auth_url or CONF.auth_url,
                cli_dir=cli_dir,
            ),
            'user': client.ManilaCLIClient(
                username=CONF.username,
                password=CONF.password,
                tenant_name=CONF.tenant_name,
                uri=CONF.auth_url,
                cli_dir=cli_dir,
            ),
        }
        return clients
