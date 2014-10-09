# Copyright 2011 OpenStack LLC.
# Copyright 2014 Mirantis, Inc.
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

"""
Command-line interface to the OpenStack Manila API.
"""

from __future__ import print_function

import argparse
import getpass
import glob
import imp
import itertools
import logging
import os
import pkgutil
import sys

import keyring
import six

from manilaclient import client
from manilaclient import exceptions as exc
import manilaclient.extension
from manilaclient.openstack.common import cliutils
from manilaclient.openstack.common import strutils
from manilaclient.v1 import shell as shell_v1
# from manilaclient.v2 import shell as shell_v2

DEFAULT_OS_SHARE_API_VERSION = "1"
DEFAULT_MANILA_ENDPOINT_TYPE = 'publicURL'
DEFAULT_MANILA_SERVICE_TYPE = 'share'

logger = logging.getLogger(__name__)


class AllowOnlyOneAliasAtATimeAction(argparse.Action):
    """Allows only one alias of argument to be used at a time."""

    def __call__(self, parser, namespace, values, option_string=None):
        # NOTE(vponomaryov): this method is redefinition of
        # argparse.Action.__call__ interface
        if getattr(namespace, self.dest) is not None:
            msg = "Only one alias is allowed at a time."
            raise argparse.ArgumentError(self, msg)
        setattr(namespace, self.dest, values)


class ManilaClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(ManilaClientArgumentParser, self).__init__(*args, **kwargs)
        # NOTE(vponomaryov): Register additional action to be used by arguments
        # with multiple aliases.
        self.register('action', 'single_alias', AllowOnlyOneAliasAtATimeAction)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, "error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                     " for more information.\n" %
                     {'errmsg': message.split(choose_from)[0],
                      'mainp': progparts[0],
                      'subp': progparts[2]})

    def _get_option_tuples(self, option_string):
        """Avoid ambiguity in argument abbreviation.

        Manilaclient uses aliases for command parameters and this method
        is used for avoiding parameter ambiguity alert.
        """
        option_tuples = super(
            ManilaClientArgumentParser, self)._get_option_tuples(option_string)
        if len(option_tuples) > 1:
            opt_strings_list = []
            opts = []
            for opt in option_tuples:
                if opt[0].option_strings not in opt_strings_list:
                    opt_strings_list.append(opt[0].option_strings)
                    opts.append(opt)
            return opts
        return option_tuples


class ManilaKeyring(keyring.backends.file.EncryptedKeyring):
    def delete_password(self, keyring_keys):
        """Delete passwords from keyring.

           Delete the passwords for given usernames of the services.

           :param keyring_key:  dictionary containing pairs {service:username}
        """
        if self._check_file():
            self._unlock()
        for key, value in six.iteritems(keyring_keys):
            super(ManilaKeyring, self).delete_password(key, value)


class SecretsHelper(object):
    """Helper for working with keyring."""

    def __init__(self, args, client):
        self.args = args
        self.client = client
        self.key = None
        self.keyring = ManilaKeyring()

    def _validate_string(self, text):
        if text is None or len(text) == 0:
            return False
        return True

    def _make_key(self):
        if self.key is not None:
            return self.key
        keys = [
            self.client.auth_url,
            self.client.user,
            self.client.projectid,
            self.client.region_name,
            self.client.endpoint_type,
            self.client.service_type,
            self.client.service_name,
            self.client.share_service_name,
        ]
        for (index, key) in enumerate(keys):
            if key is None:
                keys[index] = '?'
            else:
                keys[index] = str(keys[index])
        self.key = "/".join(keys)
        return self.key

    def _prompt_password(self, verify=True):
        """Suggest user to enter password from keyboard."""
        pw = None
        if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
            # Check for Ctl-D
            try:
                while True:
                    pw1 = getpass.getpass('OS Password: ')
                    if verify:
                        pw2 = getpass.getpass('Please verify: ')
                    else:
                        pw2 = pw1
                    if pw1 == pw2 and self._validate_string(pw1):
                        pw = pw1
                        break
            except EOFError:
                pass
        return pw

    def save(self, auth_token, management_url, tenant_id):
        """Save auth token, management url and tenant id in keyring.

        If params are different from already cached ones, save new auth token,
        management url and tenant id in keyring.

        Raise ValueError in case of empty auth_token, management_url or
        tenant_id.
        """
        if (auth_token == self.auth_token and
                management_url == self.management_url):
            # Nothing changed....
            return
        if not all([management_url, auth_token, tenant_id]):
            raise ValueError("Unable to save empty management url/auth "
                             "token")
        value = "|".join([str(auth_token),
                          str(management_url),
                          str(tenant_id)])
        self.keyring.set_password('manilaclient_auth', self._make_key(), value)

    def reset(self):
        """Delete cached password and auth token."""
        args = {'openstack': self.args.os_username,
                'manilaclient_auth': self._make_key()}
        self.keyring.delete_password(args)

    def save_password(self):
        self.keyring.set_password('openstack', self.args.os_username,
                                  self.password)

    def check_cached_password(self):
        """Check if os_password is equal to cached password."""
        if self.args.os_cache:
            cached_password = self.keyring.get_password('openstack',
                                                        self.args.os_username)
            cached_token = self.keyring.get_password('manilaclient_auth',
                                                     self._make_key())
            if cached_password and self.password != cached_password:
                return False
            if cached_token and not cached_password:
                return False
        return True

    @property
    def password(self):
        """Return user password.

        Return os_password value or suggest user to enter new password from
        keyboard.
        """
        password = None
        if self._validate_string(self.args.os_password):
            password = self.args.os_password
        else:
            verify_pass = strutils.bool_from_string(
                cliutils.env("OS_VERIFY_PASSWORD", default=False))
            password = self._prompt_password(verify_pass)
        if not password:
            raise exc.CommandError(
                'Expecting a password provided via either '
                '--os-password, env[OS_PASSWORD], or '
                'prompted response')
        return password

    @property
    def management_url(self):
        """Return cached management url.

        If os_cache enabled and management url already cached, return
        management url. Otherwise return None.
        """
        if not self.args.os_cache:
            return None
        management_url = None
        block = self.keyring.get_password('manilaclient_auth',
                                          self._make_key())
        if block:
            _token, management_url, _tenant_id = block.split('|', 2)
        return management_url

    @property
    def auth_token(self):
        """Return cached auth token.

        If os_cache enabled and auth token already cached, return auth token.
        Otherwise return None.
        """
        if not self.args.os_cache:
            return None
        token = None
        block = self.keyring.get_password('manilaclient_auth',
                                          self._make_key())
        if block:
            token, _management_url, _tenant_id = block.split('|', 2)
        return token

    @property
    def tenant_id(self):
        """Return cached tenant id.

        If os_cache enabled and tenant id already cached, return tenant id.
        Otherwise return None.
        """
        if not self.args.os_cache:
            return None
        tenant_id = None
        block = self.keyring.get_password('manilaclient_auth',
                                          self._make_key())
        if block:
            _token, _management_url, tenant_id = block.split('|', 2)
        return tenant_id


class OpenStackManilaShell(object):

    def get_base_parser(self):
        parser = ManilaClientArgumentParser(
            prog='manila',
            description=__doc__.strip(),
            epilog='See "manila help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--version',
                            action='version',
                            version=manilaclient.__version__)

        parser.add_argument('--debug',
                            action='store_true',
                            default=cliutils.env('manilaclient_DEBUG',
                                                 default=False),
                            help="Print debugging output.")

        parser.add_argument('--os-cache',
                            default=cliutils.env('OS_CACHE', default=False),
                            action='store_true',
                            help='Use the auth token cache. '
                                 'Defaults to env[OS_CACHE].')

        parser.add_argument('--os-reset-cache',
                            default=False,
                            action='store_true',
                            help='Delete cached password and auth token.')

        parser.add_argument('--os-username',
                            metavar='<auth-user-name>',
                            default=cliutils.env('OS_USERNAME',
                                                 'MANILA_USERNAME'),
                            help='Defaults to env[OS_USERNAME].')
        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
                            metavar='<auth-password>',
                            default=cliutils.env('OS_PASSWORD',
                                                 'MANILA_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD].')
        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            metavar='<auth-tenant-name>',
                            default=cliutils.env('OS_TENANT_NAME',
                                                 'MANILA_PROJECT_ID'),
                            help='Defaults to env[OS_TENANT_NAME].')
        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
                            metavar='<auth-tenant-id>',
                            default=cliutils.env('OS_TENANT_ID',
                                                 'MANILA_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID].')
        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            metavar='<auth-url>',
                            default=cliutils.env('OS_AUTH_URL',
                                                 'MANILA_URL'),
                            help='Defaults to env[OS_AUTH_URL].')
        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-region-name',
                            metavar='<region-name>',
                            default=cliutils.env('OS_REGION_NAME',
                                                 'MANILA_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME].')
        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--service-type',
                            metavar='<service-type>',
                            help='Defaults to compute for most actions.')
        parser.add_argument('--service_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--service-name',
                            metavar='<service-name>',
                            default=cliutils.env('MANILA_SERVICE_NAME'),
                            help='Defaults to env[MANILA_SERVICE_NAME].')
        parser.add_argument('--service_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--share-service-name',
                            metavar='<share-service-name>',
                            default=cliutils.env('MANILA_share_service_name'),
                            help='Defaults to env[MANILA_share_service_name].')
        parser.add_argument('--share_service_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--endpoint-type',
                            metavar='<endpoint-type>',
                            default=cliutils.env(
                                'MANILA_ENDPOINT_TYPE',
                                default=DEFAULT_MANILA_ENDPOINT_TYPE),
                            help='Defaults to env[MANILA_ENDPOINT_TYPE] or '
                            + DEFAULT_MANILA_ENDPOINT_TYPE + '.')
        parser.add_argument('--endpoint_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-share-api-version',
                            metavar='<compute-api-ver>',
                            default=cliutils.env(
                                'OS_SHARE_API_VERSION',
                                default=DEFAULT_OS_SHARE_API_VERSION),
                            help='Accepts 1 or 2, defaults '
                                 'to env[OS_SHARE_API_VERSION].')
        parser.add_argument('--os_share_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-cacert',
                            metavar='<ca-certificate>',
                            default=cliutils.env('OS_CACERT', default=None),
                            help='Specify a CA bundle file to use in '
                            'verifying a TLS (https) server certificate. '
                            'Defaults to env[OS_CACERT].')

        parser.add_argument('--insecure',
                            default=cliutils.env('manilaclient_INSECURE',
                                                 default=False),
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--retries',
                            metavar='<retries>',
                            type=int,
                            default=0,
                            help='Number of retries.')

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '1.1': shell_v1,
            }[version]
        except KeyError:
            actions_module = shell_v1

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        for extension in self.extensions:
            self._find_actions(subparsers, extension.module)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _discover_extensions(self, version):
        extensions = []
        for name, module in itertools.chain(
                self._discover_via_python_path(version),
                self._discover_via_contrib_path(version)):

            extension = manilaclient.extension.Extension(name, module)
            extensions.append(extension)

        return extensions

    def _discover_via_python_path(self, version):
        for (module_loader, name, ispkg) in pkgutil.iter_modules():
            if name.endswith('python_manilaclient_ext'):
                if not hasattr(module_loader, 'load_module'):
                    # Python 2.6 compat: actually get an ImpImporter obj
                    module_loader = module_loader.find_module(name)

                module = module_loader.load_module(name)
                yield name, module

    def _discover_via_contrib_path(self, version):
        module_path = os.path.dirname(os.path.abspath(__file__))
        version_str = "v%s" % version.replace('.', '_')
        ext_path = os.path.join(module_path, version_str, 'contrib')
        ext_glob = os.path.join(ext_path, "*.py")

        for ext_path in glob.iglob(ext_glob):
            name = os.path.basename(ext_path)[:-3]

            if name == "__init__":
                continue

            module = imp.load_source(name, ext_path)
            yield name, module

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter)

        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip()
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)

            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS,)

            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if not debug:
            return

        streamhandler = logging.StreamHandler()
        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        streamhandler.setFormatter(logging.Formatter(streamformat))
        logger.setLevel(logging.DEBUG)
        logger.addHandler(streamhandler)

    def main(self, argv):
        # Parse args once to find version and debug settings
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self.setup_debugging(options.debug)

        # build available subcommands based on version
        self.extensions = self._discover_extensions(
            options.os_share_api_version)
        self._run_extension_hooks('__pre_parse_args__')

        subcommand_parser = self.get_subcommand_parser(
            options.os_share_api_version)
        self.parser = subcommand_parser

        if options.help or not argv:
            subcommand_parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)
        self._run_extension_hooks('__post_parse_args__', args)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        (os_username, os_password, os_tenant_name, os_auth_url,
         os_region_name, os_tenant_id, endpoint_type, insecure,
         service_type, service_name, share_service_name,
         cacert, os_cache, os_reset_cache) = (
             args.os_username, args.os_password, args.os_tenant_name,
             args.os_auth_url, args.os_region_name, args.os_tenant_id,
             args.endpoint_type, args.insecure, args.service_type,
             args.service_name, args.share_service_name,
             args.os_cacert, args.os_cache, args.os_reset_cache)

        if not endpoint_type:
            endpoint_type = DEFAULT_MANILA_ENDPOINT_TYPE

        if not service_type:
            service_type = DEFAULT_MANILA_SERVICE_TYPE
            service_type = cliutils.get_service_type(args.func) or service_type

        # FIXME(usrleon): Here should be restrict for project id same as
        # for os_username or os_password but for compatibility it is not.

        if not cliutils.isunauthenticated(args.func):
            if not os_username:
                raise exc.CommandError(
                    "You must provide a username "
                    "via either --os-username or env[OS_USERNAME]")

            if not (os_tenant_name or os_tenant_id):
                raise exc.CommandError("You must provide a tenant_id "
                                       "via either --os-tenant-id or "
                                       "env[OS_TENANT_ID]")

            if not os_auth_url:
                raise exc.CommandError(
                    "You must provide an auth url "
                    "via either --os-auth-url or env[OS_AUTH_URL]")

        if not (os_tenant_name or os_tenant_id):
            raise exc.CommandError(
                "You must provide a tenant_id "
                "via either --os-tenant-id or env[OS_TENANT_ID]")

        if not os_auth_url:
            raise exc.CommandError(
                "You must provide an auth url "
                "via either --os-auth-url or env[OS_AUTH_URL]")

        self.cs = client.Client(options.os_share_api_version, os_username,
                                os_password, os_tenant_name, os_auth_url,
                                insecure, region_name=os_region_name,
                                tenant_id=os_tenant_id,
                                endpoint_type=endpoint_type,
                                extensions=self.extensions,
                                service_type=service_type,
                                service_name=service_name,
                                share_service_name=share_service_name,
                                retries=options.retries,
                                http_log_debug=args.debug,
                                cacert=cacert,
                                os_cache=os_cache)
        if not cliutils.isunauthenticated(args.func):
            helper = SecretsHelper(args, self.cs.client)
            if os_reset_cache:
                helper.reset()
            self.cs.client.keyring_saver = helper
            if (helper.tenant_id and helper.auth_token and
                    helper.management_url and
                    helper.check_cached_password()):
                self.cs.client.tenant_id = helper.tenant_id
                self.cs.client.auth_token = helper.auth_token
                self.cs.client.management_url = helper.management_url
            else:
                self.cs.client.password = helper.password
                try:
                    self.cs.authenticate()
                except exc.Unauthorized:
                    raise exc.CommandError("Invalid OpenStack Manila "
                                           "credentials.")
                except exc.AuthorizationFailure:
                    raise exc.CommandError("Unable to authorize user")

        args.func(self.cs, args)

    def _run_extension_hooks(self, hook_type, *args, **kwargs):
        """Run hooks for all registered extensions."""
        for extension in self.extensions:
            extension.run_hooks(hook_type, *args, **kwargs)

    def do_bash_completion(self, args):
        """Print arguments for bash_completion.

        Prints all of the commands and options to stdout so that the
        manila.bash_completion script doesn't have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in list(self.subcommands.items()):
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions:
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @cliutils.arg('command', metavar='<subcommand>', nargs='?',
                  help='Display help for <subcommand>')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        if sys.version_info >= (3, 0):
            OpenStackManilaShell().main(sys.argv[1:])
        else:
            OpenStackManilaShell().main(
                map(strutils.safe_decode, sys.argv[1:]))
    except KeyboardInterrupt:
        print("... terminating manila client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logger.debug(e, exc_info=1)
        message = e.message
        if not isinstance(message, six.string_types):
            message = str(message)
        print("ERROR: %s" % strutils.safe_encode(message), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
