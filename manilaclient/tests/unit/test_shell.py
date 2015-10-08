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

import re
import sys

import ddt
import fixtures
import mock
from six import moves
from testtools import matchers

from manilaclient.common import constants
from manilaclient import exceptions
from manilaclient import shell
from manilaclient.tests.unit import utils


@ddt.ddt
class OpenstackManilaShellTest(utils.TestCase):

    FAKE_ENV = {
        'OS_USERNAME': 'username',
        'OS_PASSWORD': 'password',
        'OS_TENANT_NAME': 'tenant_name',
        'OS_AUTH_URL': 'http://no.where',
    }

    # Patch os.environ to avoid required auth info.
    def set_env_vars(self, env_vars):
        for k, v in env_vars.items():
            self.useFixture(fixtures.EnvironmentVariable(k, v))

    def shell(self, argstr):
        orig = sys.stdout
        try:
            sys.stdout = moves.StringIO()
            _shell = shell.OpenStackManilaShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig

        return out

    @ddt.data(
        {},
        {'OS_AUTH_URL': 'http://foo.bar'},
        {'OS_AUTH_URL': 'http://foo.bar', 'OS_USERNAME': 'foo'},
        {'OS_AUTH_URL': 'http://foo.bar', 'OS_USERNAME': 'foo_user',
         'OS_PASSWORD': 'foo_password'},
        {'OS_TENANT_NAME': 'foo_tenant', 'OS_USERNAME': 'foo_user',
         'OS_PASSWORD': 'foo_password'},
    )
    def test_main_failure(self, env_vars):
        self.set_env_vars(env_vars)
        with mock.patch.object(shell, 'client') as mock_client:
            self.assertRaises(exceptions.CommandError, self.shell, 'list')
            self.assertFalse(mock_client.Client.called)

    def test_main_success(self):
        env_vars = {
            'OS_AUTH_URL': 'http://foo.bar',
            'OS_USERNAME': 'foo_username',
            'OS_USER_ID': 'foo_user_id',
            'OS_PASSWORD': 'foo_password',
            'OS_TENANT_NAME': 'foo_tenant',
            'OS_TENANT_ID': 'foo_tenant_id',
            'OS_PROJECT_NAME': 'foo_project',
            'OS_PROJECT_ID': 'foo_project_id',
            'OS_PROJECT_DOMAIN_ID': 'foo_project_domain_id',
            'OS_PROJECT_DOMAIN_NAME': 'foo_project_domain_name',
            'OS_PROJECT_DOMAIN_ID': 'foo_project_domain_id',
            'OS_USER_DOMAIN_NAME': 'foo_user_domain_name',
            'OS_USER_DOMAIN_ID': 'foo_user_domain_id',
            'OS_CERT': 'foo_cert',
        }
        self.set_env_vars(env_vars)
        with mock.patch.object(shell, 'client') as mock_client:

            self.shell('list')

            mock_client.Client.assert_called_once_with(
                constants.MAX_API_VERSION,
                username=env_vars['OS_USERNAME'],
                password=env_vars['OS_PASSWORD'],
                project_name=env_vars['OS_PROJECT_NAME'],
                auth_url=env_vars['OS_AUTH_URL'],
                insecure=False,
                region_name='',
                tenant_id=env_vars['OS_PROJECT_ID'],
                endpoint_type='publicURL',
                extensions=mock.ANY,
                service_type='sharev2',
                service_name='',
                retries=0,
                http_log_debug=False,
                cacert=None,
                use_keyring=False,
                force_new_token=False,
                api_version=constants.MAX_API_VERSION,
                user_id=env_vars['OS_USER_ID'],
                user_domain_id=env_vars['OS_USER_DOMAIN_ID'],
                user_domain_name=env_vars['OS_USER_DOMAIN_NAME'],
                project_domain_id=env_vars['OS_PROJECT_DOMAIN_ID'],
                project_domain_name=env_vars['OS_PROJECT_DOMAIN_NAME'],
                cert=env_vars['OS_CERT'],
            )

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, self.shell, 'help foofoo')

    def test_help(self):
        required = [
            '.*?^usage: ',
            '.*?^\s+create\s+Creates a new share '
            '\(NFS, CIFS, GlusterFS or HDFS\).',
            '.*?(?m)^See "manila help COMMAND" for help '
            'on a specific command.',
        ]
        help_text = self.shell('help')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_help_on_subcommand(self):
        required = [
            '.*?^usage: manila list',
            '.*?(?m)^List NAS shares with filters.',
        ]
        help_text = self.shell('help list')
        for r in required:
            self.assertThat(help_text,
                            matchers.MatchesRegex(r, re.DOTALL | re.MULTILINE))

    def test_common_args_in_help_message(self):
        expected_args = (
            '--version', '', '--debug', '--os-cache', '--os-reset-cache',
            '--os-user-id', '--os-username', '--os-password',
            '--os-tenant-name', '--os-project-name', '--os-tenant-id',
            '--os-project-id', '--os-user-domain-id', '--os-user-domain-name',
            '--os-project-domain-id', '--os-project-domain-name',
            '--os-auth-url', '--os-region-name', '--service-type',
            '--service-name', '--share-service-name', '--endpoint-type',
            '--os-share-api-version', '--os-cacert', '--retries', '--os-cert',
        )

        help_text = self.shell('help')

        for expected_arg in expected_args:
            self.assertIn(expected_arg, help_text)
