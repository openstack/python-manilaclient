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

import fixtures
import mock
import requests

from manilaclient import client
from manilaclient import exceptions
from manilaclient.openstack.common import jsonutils
from manilaclient import shell
from manilaclient.v1 import client as client_v1
from manilaclient.v1 import shell as shell_v1
from tests import utils
from tests.v1 import fakes


class ShellTest(utils.TestCase):

    FAKE_ENV = {
        'MANILA_USERNAME': 'username',
        'MANILA_PASSWORD': 'password',
        'MANILA_PROJECT_ID': 'project_id',
        'OS_SHARE_API_VERSION': '2',
        'MANILA_URL': 'http://no.where',
    }

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        super(ShellTest, self).setUp()
        for var in self.FAKE_ENV:
            self.useFixture(fixtures.EnvironmentVariable(var,
                                                         self.FAKE_ENV[var]))

        self.shell = shell.OpenStackManilaShell()

        # HACK(bcwaldon): replace this when we start using stubs
        self.old_get_client_class = client.get_client_class
        client.get_client_class = lambda *_: fakes.FakeClient

    def tearDown(self):
        # For some method like test_image_meta_bad_action we are
        # testing a SystemExit to be thrown and object self.shell has
        # no time to get instantatiated which is OK in this case, so
        # we make sure the method is there before launching it.
        if hasattr(self.shell, 'cs') and hasattr(self.shell.cs,
                                                 'clear_callstack'):
            self.shell.cs.clear_callstack()

        # HACK(bcwaldon): replace this when we start using stubs
        client.get_client_class = self.old_get_client_class
        super(ShellTest, self).tearDown()

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_list(self):
        self.run_command('list')
        # NOTE(jdg): we default to detail currently
        self.assert_called('GET', '/shares/detail')

    def test_list_filter_status(self):
        self.run_command('list --status=available')
        self.assert_called('GET', '/shares/detail?status=available')

    def test_list_filter_name(self):
        self.run_command('list --name=1234')
        self.assert_called('GET', '/shares/detail?name=1234')

    def test_list_all_tenants(self):
        self.run_command('list --all-tenants=1')
        self.assert_called('GET', '/shares/detail?all_tenants=1')

    def test_list_filter_share_server_id(self):
        self.run_command('list --share-server-id=1234')
        self.assert_called('GET', '/shares/detail?share_server_id=1234')

    def test_show(self):
        self.run_command('show 1234')
        self.assert_called('GET', '/shares/1234')

    def test_delete(self):
        self.run_command('delete 1234')
        self.assert_called('DELETE', '/shares/1234')

    def test_delete_not_found(self):
        self.assertRaises(
            exceptions.CommandError,
            self.run_command,
            'delete fake-not-found'
        )

    def test_snapshot_list_filter_share_id(self):
        self.run_command('snapshot-list --share-id=1234')
        self.assert_called('GET', '/snapshots/detail?share_id=1234')

    def test_snapshot_list_filter_status_and_share_id(self):
        self.run_command('snapshot-list --status=available --share-id=1234')
        self.assert_called('GET', '/snapshots/detail?'
                           'share_id=1234&status=available')

    def test_rename(self):
        # basic rename with positional agruments
        self.run_command('rename 1234 new-name')
        expected = {'share': {'display_name': 'new-name'}}
        self.assert_called('PUT', '/shares/1234', body=expected)
        # change description only
        self.run_command('rename 1234 --description=new-description')
        expected = {'share': {'display_description': 'new-description'}}
        self.assert_called('PUT', '/shares/1234', body=expected)
        # rename and change description
        self.run_command('rename 1234 new-name '
                         '--description=new-description')
        expected = {'share': {
            'display_name': 'new-name',
            'display_description': 'new-description',
        }}
        self.assert_called('PUT', '/shares/1234', body=expected)
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'rename 1234')

    def test_rename_snapshot(self):
        # basic rename with positional agruments
        self.run_command('snapshot-rename 1234 new-name')
        expected = {'snapshot': {'display_name': 'new-name'}}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # change description only
        self.run_command('snapshot-rename 1234 '
                         '--description=new-description')
        expected = {'snapshot': {'display_description': 'new-description'}}

        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # snapshot-rename and change description
        self.run_command('snapshot-rename 1234 new-name '
                         '--description=new-description')
        expected = {'snapshot': {
            'display_name': 'new-name',
            'display_description': 'new-description',
        }}
        self.assert_called('PUT', '/snapshots/1234', body=expected)
        # noop, the only all will be the lookup
        self.assertRaises(exceptions.CommandError,
                          self.run_command, 'rename 1234')

    def test_set_metadata_set(self):
        self.run_command('metadata 1234 set key1=val1 key2=val2')
        self.assert_called('POST', '/shares/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_set_metadata_delete_dict(self):
        self.run_command('metadata 1234 unset key1=val1 key2=val2')
        self.assert_called('DELETE', '/shares/1234/metadata/key1')
        self.assert_called('DELETE', '/shares/1234/metadata/key2', pos=-2)

    def test_set_metadata_delete_keys(self):
        self.run_command('metadata 1234 unset key1 key2')
        self.assert_called('DELETE', '/shares/1234/metadata/key1')
        self.assert_called('DELETE', '/shares/1234/metadata/key2', pos=-2)

    def test_share_metadata_update_all(self):
        self.run_command('metadata-update-all 1234 key1=val1 key2=val2')
        self.assert_called('PUT', '/shares/1234/metadata',
                           {'metadata': {'key1': 'val1', 'key2': 'val2'}})

    def test_extract_metadata(self):
        # mimic the result of argparse's parse_args() method
        class Arguments:
            def __init__(self, metadata=[]):
                self.metadata = metadata

        inputs = [
            ([], {}),
            (["key=value"], {"key": "value"}),
            (["key"], {"key": None}),
            (["k1=v1", "k2=v2"], {"k1": "v1", "k2": "v2"}),
            (["k1=v1", "k2"], {"k1": "v1", "k2": None}),
            (["k1", "k2=v2"], {"k1": None, "k2": "v2"})
        ]

        for input in inputs:
            args = Arguments(metadata=input[0])
            self.assertEqual(shell_v1._extract_metadata(args), input[1])

    def test_reset_state(self):
        self.run_command('reset-state 1234')
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called('POST', '/shares/1234/action', body=expected)

    def test_reset_state_with_flag(self):
        self.run_command('reset-state --state error 1234')
        expected = {'os-reset_status': {'status': 'error'}}
        self.assert_called('POST', '/shares/1234/action', body=expected)

    def test_snapshot_reset_state(self):
        self.run_command('snapshot-reset-state 1234')
        expected = {'os-reset_status': {'status': 'available'}}
        self.assert_called('POST', '/snapshots/1234/action', body=expected)

    def test_snapshot_reset_state_with_flag(self):
        self.run_command('snapshot-reset-state --state error 1234')
        expected = {'os-reset_status': {'status': 'error'}}
        self.assert_called('POST', '/snapshots/1234/action', body=expected)

    def test_share_network_security_service_add(self):
        self.run_command('share-network-security-service-add fake_share_nw '
                         'fake_security_service')
        self.assert_called(
            'POST',
            '/share-networks/1234/action',
        )

    def test_share_network_security_service_remove(self):
        self.run_command('share-network-security-service-remove fake_share_nw '
                         'fake_security_service')
        self.assert_called(
            'POST',
            '/share-networks/1234/action',
        )

    def test_share_network_security_service_list_by_name(self):
        self.run_command('share-network-security-service-list fake_share_nw')
        self.assert_called(
            'GET',
            '/security-services/detail?share_network_id=1234',
        )

    def test_share_network_security_service_list_by_name_not_found(self):
        self.assertRaises(
            exceptions.CommandError,
            self.run_command,
            'share-network-security-service-list inexistent_share_nw',
        )

    def test_share_network_security_service_list_by_name_multiple(self):
        self.assertRaises(
            exceptions.CommandError,
            self.run_command,
            'share-network-security-service-list duplicated_name',
        )

    def test_share_network_security_service_list_by_id(self):
        self.run_command('share-network-security-service-list 1111')
        self.assert_called(
            'GET',
            '/security-services/detail?share_network_id=1111',
        )

    def test_share_server_delete(self):
        self.run_command('share-server-delete 1234')
        self.assert_called('DELETE', '/share-servers/1234')

    def test_create_share(self):
        # Use only required fields
        self.run_command("create nfs 1")
        expected = {
            "share": {
                "volume_type": None,
                "name": None,
                "snapshot_id": None,
                "description": None,
                "metadata": {},
                "share_proto": "nfs",
                "share_network_id": None,
                "size": 1,
            }
        }
        self.assert_called("POST", "/shares", body=expected)

    def test_create_with_share_network(self):
        # Except required fields added share network
        sn = "fake-share-network"
        with mock.patch.object(shell_v1, "_find_share_network",
                               mock.Mock(return_value=sn)):
            self.run_command("create nfs 1 --share-network %s" % sn)
            expected = {
                "share": {
                    "volume_type": None,
                    "name": None,
                    "snapshot_id": None,
                    "description": None,
                    "metadata": {},
                    "share_proto": "nfs",
                    "share_network_id": sn,
                    "size": 1,
                }
            }
            self.assert_called("POST", "/shares", body=expected)
            shell_v1._find_share_network.assert_called_once_with(mock.ANY, sn)

    def test_create_with_metadata(self):
        # Except required fields added metadata
        self.run_command("create nfs 1 --metadata key1=value1 key2=value2")
        expected = {
            "share": {
                "volume_type": None,
                "name": None,
                "snapshot_id": None,
                "description": None,
                "metadata": {"key1": "value1", "key2": "value2"},
                "share_proto": "nfs",
                "share_network_id": None,
                "size": 1,
            }
        }
        self.assert_called("POST", "/shares", body=expected)

    def test_allow_access_cert(self):
        self.run_command("access-allow 1234 cert client.example.com")

        expected = {
            "os-allow_access": {
                "access_type": "cert",
                "access_to": "client.example.com",
            }
        }
        self.assert_called("POST", "/shares/1234/action", body=expected)

    def test_allow_access_cert_error_gt64(self):
        common_name = 'x' * 65
        self.assertRaises(exceptions.CommandError, self.run_command,
                          ("access-allow 1234 cert %s" % common_name))

    def test_allow_access_cert_error_zero(self):
        cmd = mock.Mock()
        cmd.split = mock.Mock(side_effect=lambda: ['access-allow', '1234',
                                                   'cert', ''])

        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

        cmd.split.assert_called_once_with()

    def test_allow_access_cert_error_whitespace(self):
        cmd = mock.Mock()
        cmd.split = mock.Mock(side_effect=lambda: ['access-allow', '1234',
                                                   'cert', ' '])

        self.assertRaises(exceptions.CommandError, self.run_command, cmd)

        cmd.split.assert_called_once_with()

    @mock.patch.object(fakes.FakeClient, 'authenticate', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, '_make_key', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, 'password', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, 'check_cached_password',
                       mock.Mock())
    def test_os_cache_enabled_keys_saved_password_not_changed(self):
        shell.SecretsHelper.tenant_id = 'fake'
        shell.SecretsHelper.auth_token = 'fake'
        shell.SecretsHelper.management_url = 'fake'
        self.run_command('--os-cache list')
        self.assertFalse(shell.SecretsHelper.password.called)
        self.assertFalse(fakes.FakeClient.authenticate.called)

    @mock.patch.object(shell.SecretsHelper, '_validate_string', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, '_prompt_password', mock.Mock())
    @mock.patch.object(shell.ManilaKeyring, 'get_password', mock.Mock())
    def test_os_cache_enabled_keys_not_saved_with_password(self):
        shell.SecretsHelper._validate_string.return_value = True
        shell.ManilaKeyring.get_password.return_value = None
        shell.SecretsHelper.tenant_id = None
        shell.SecretsHelper.auth_token = None
        shell.SecretsHelper.management_url = None
        self.run_command('--os-cache list')
        self.assertFalse(shell.SecretsHelper._prompt_password.called)
        shell.SecretsHelper._validate_string.assert_called_once_with(
            'password')

    @mock.patch.object(shell.SecretsHelper, '_prompt_password', mock.Mock())
    @mock.patch.object(shell.ManilaKeyring, 'get_password', mock.Mock())
    def test_os_cache_enabled_keys_not_saved_no_password(self):
        shell.ManilaKeyring.get_password.return_value = None
        shell.SecretsHelper._prompt_password.return_value = 'password'
        self.useFixture(fixtures.EnvironmentVariable('MANILA_PASSWORD', ''))
        shell.SecretsHelper.tenant_id = None
        shell.SecretsHelper.auth_token = None
        shell.SecretsHelper.management_url = None
        self.run_command('--os-cache list')
        self.assertTrue(shell.SecretsHelper._prompt_password.called)

    @mock.patch.object(shell.SecretsHelper, '_validate_string', mock.Mock())
    @mock.patch.object(shell.ManilaKeyring, 'get_password', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, 'reset', mock.Mock())
    def test_os_cache_enabled_keys_reset_cached_password(self):
        shell.ManilaKeyring.get_password.return_value = 'old_password'
        shell.SecretsHelper._validate_string.return_value = True
        shell.SecretsHelper.tenant_id = None
        shell.SecretsHelper.auth_token = None
        shell.SecretsHelper.management_url = None
        self.run_command('--os-cache --os-reset-cache list')
        shell.SecretsHelper._validate_string.assert_called_once_with(
            'password')
        shell.SecretsHelper.reset.assert_called_once_with()

    @mock.patch.object(shell.SecretsHelper, '_validate_string', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, 'reset', mock.Mock())
    def test_os_cache_disabled_keys_reset_cached_password(self):
        shell.SecretsHelper._validate_string.return_value = True
        self.run_command('--os-reset-cache list')
        shell.SecretsHelper._validate_string.assert_called_once_with(
            'password')
        shell.SecretsHelper.reset.assert_called_once_with()

    @mock.patch.object(fakes.FakeClient, 'authenticate', mock.Mock())
    @mock.patch.object(shell.ManilaKeyring, 'get_password', mock.Mock())
    @mock.patch.object(shell.SecretsHelper, '_make_key', mock.Mock())
    def test_os_cache_enabled_os_password_differs_from_the_cached_one(self):
        def _fake_get_password(service, username):
            if service == 'openstack':
                return 'old_cached_password'
            else:
                return 'old_cached_token'
        shell.SecretsHelper.tenant_id = 'fake'
        shell.SecretsHelper.auth_token = 'fake'
        shell.SecretsHelper.management_url = 'fake'
        self.run_command('--os-cache list')
        fakes.FakeClient.authenticate.assert_called_once_with()

    @mock.patch.object(requests, 'request', mock.Mock())
    @mock.patch.object(client.HTTPClient, '_save_keys', mock.Mock())
    def test_os_cache_token_expired(self):
        def _fake_request(method, url, **kwargs):
            headers = None
            if url == 'new_url/shares/detail':
                resp_text = {"shares": []}
                return utils.TestResponse({
                    "status_code": 200,
                    "text": jsonutils.dumps(resp_text),
                })
            elif url == 'fake/shares/detail':
                resp_text = {"unauthorized": {"message": "Unauthorized",
                                              "code": "401"}}
                return utils.TestResponse({
                    "status_code": 401,
                    "text": jsonutils.dumps(resp_text),
                })
            else:
                headers = {
                    'x-server-management-url': 'new_url',
                    'x-auth-token': 'new_token',
                }
                resp_text = 'some_text'
                return utils.TestResponse({
                    "status_code": 200,
                    "text": jsonutils.dumps(resp_text),
                    "headers": headers
                })

        client.get_client_class = lambda *_: client_v1.Client
        shell.SecretsHelper.tenant_id = 'fake'
        shell.SecretsHelper.auth_token = 'fake'
        shell.SecretsHelper.management_url = 'fake'
        requests.request.side_effect = _fake_request

        self.run_command('--os-cache list')

        client.HTTPClient._save_keys.assert_called_once_with()
        expected_headers = {
            'X-Auth-Project-Id': 'project_id',
            'User-Agent': 'python-manilaclient',
            'Accept': 'application/json',
            'X-Auth-Token': 'new_token'}
        requests.request.assert_called_with(
            'GET',
            'new_url/shares/detail',
            headers=expected_headers,
            verify=True,
        )


class SecretsHelperTestCase(utils.TestCase):
    def setUp(self):
        super(SecretsHelperTestCase, self).setUp()
        self.cs = client.Client(1, 'user', 'password',
                                project_id='project',
                                auth_url='http://111.11.11.11:5000',
                                region_name='region',
                                endpoint_type='publicURL',
                                service_type='share',
                                service_name='fake',
                                share_service_name='fake')
        self.args = mock.Mock()
        self.args.os_cache = True
        self.args.reset_cached_password = False
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        mock.patch.object(shell.ManilaKeyring, 'set_password',
                          mock.Mock()).start()
        mock.patch.object(shell.ManilaKeyring, 'get_password', mock.Mock(
            return_value='fake_token|fake_url|fake_tenant_id')).start()
        self.addCleanup(mock.patch.stopall)

    def test_validate_string_empty_string(self):
        self.assertFalse(self.helper._validate_string(''))

    def test_validate_string_void_string(self):
        self.assertFalse(self.helper._validate_string(None))

    def test_validate_string_good_string(self):
        self.assertTrue(self.helper._validate_string('this is a string'))

    def test_make_key(self):
        expected_key = ('http://111.11.11.11:5000/user/project/region/'
                        'publicURL/share/fake/fake')
        self.assertEqual(self.helper._make_key(), expected_key)

    def test_make_key_missing_attrs(self):
        self.cs.client.service_name = self.cs.client.region_name = None
        expected_key = ('http://111.11.11.11:5000/user/project/?/'
                        'publicURL/share/?/fake')
        self.assertEqual(self.helper._make_key(), expected_key)

    def test_save(self):
        shell.ManilaKeyring.get_password.return_value = ''
        expected_key = ('http://111.11.11.11:5000/user/project/region/'
                        'publicURL/share/fake/fake')
        self.helper.save('fake_token', 'fake_url', 'fake_tenant_id')
        shell.ManilaKeyring.set_password.assert_called_once_with(
            'manilaclient_auth',
            expected_key,
            'fake_token|fake_url|fake_tenant_id',
        )

    def test_save_params_already_cached(self):
        self.helper.save('fake_token', 'fake_url', 'fake_tenant_id')
        self.assertFalse(shell.ManilaKeyring.set_password.called)

    def test_save_missing_params(self):
        self.assertRaises(ValueError, self.helper.save, None, 'fake_url',
                          'fake_tenant_id')

    def test_password_os_password(self):
        self.args.os_password = 'fake_password'
        self.args.os_username = 'fake_username'
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        self.assertEqual(self.helper.password, 'fake_password')

    @mock.patch.object(shell.SecretsHelper, '_prompt_password', mock.Mock())
    def test_password_from_keyboard(self):
        self.args.os_password = ''
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        shell.SecretsHelper._prompt_password.return_value = None
        self.assertRaises(exceptions.CommandError, getattr, self.helper,
                          'password')

    def test_management_url_os_cache_false(self):
        self.args.os_cache = False
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        self.assertIsNone(self.helper.management_url)

    def test_management_url_os_cache_true(self):
        self.assertEqual(self.helper.management_url, 'fake_url')
        expected_key = ('http://111.11.11.11:5000/user/project/region/'
                        'publicURL/share/fake/fake')
        shell.ManilaKeyring.get_password.assert_called_once_with(
            'manilaclient_auth', expected_key)

    def test_auth_token_os_cache_false(self):
        self.args.os_cache = False
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        self.assertIsNone(self.helper.auth_token)

    def test_auth_token_os_cache_true(self):
        self.assertEqual(self.helper.auth_token, 'fake_token')
        expected_key = ('http://111.11.11.11:5000/user/project/region/'
                        'publicURL/share/fake/fake')
        shell.ManilaKeyring.get_password.assert_called_once_with(
            'manilaclient_auth', expected_key)

    def test_tenant_id_os_cache_false(self):
        self.args.os_cache = False
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        self.assertIsNone(self.helper.tenant_id)

    def test_tenant_id_os_cache_true(self):
        self.assertEqual(self.helper.tenant_id, 'fake_tenant_id')
        expected_key = ('http://111.11.11.11:5000/user/project/region/'
                        'publicURL/share/fake/fake')
        shell.ManilaKeyring.get_password.assert_called_once_with(
            'manilaclient_auth', expected_key)

    def test_check_cached_password_os_cache_false(self):
        self.args.os_cache = False
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        self.assertTrue(self.helper.check_cached_password())

    def test_check_cached_password_same_passwords(self):
        self.args.os_password = 'user_password'
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        shell.ManilaKeyring.get_password.return_value = 'user_password'
        self.assertTrue(self.helper.check_cached_password())

    def test_check_cached_password_no_cache(self):
        shell.ManilaKeyring.get_password.return_value = None
        self.assertTrue(self.helper.check_cached_password())

    def test_check_cached_password_different_passwords(self):
        self.args.os_password = 'new_user_password'
        self.helper = shell.SecretsHelper(self.args, self.cs.client)
        shell.ManilaKeyring.get_password.return_value = 'cached_password'
        self.assertFalse(self.helper.check_cached_password())

    def test_check_cached_password_cached_password_deleted(self):
        def _fake_get_password(service, username):
            if service == 'openstack':
                return None
            else:
                return 'fake_token'

        shell.ManilaKeyring.get_password.side_effect = _fake_get_password
        self.assertFalse(self.helper.check_cached_password())
