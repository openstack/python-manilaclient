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

import copy
import os

from oslo_config import cfg
import oslo_log._options as log_options

from manilaclient import api_versions

# 1. Define opts

# "auth_opts" are used by functional tests that are located in
# directory "%project_root%/manilaclient/tests/functional"
auth_opts = [
    cfg.StrOpt("username",
               default=None,
               help="This should be the username of a user WITHOUT "
                    "administrative privileges."),
    cfg.StrOpt("tenant_name",
               default=None,
               help="The non-administrative user's tenant name."),
    cfg.StrOpt("password",
               default=None,
               help="The non-administrative user's password."),
    cfg.StrOpt("auth_url",
               default=None,
               help="URL for where to find the OpenStack Identity public "
                    "API endpoint."),
    cfg.StrOpt("admin_username",
               default=None,
               help="This should be the username of a user WITH "
                    "administrative privileges."),
    cfg.StrOpt("admin_tenant_name",
               default=None,
               help="The administrative user's tenant name."),
    cfg.StrOpt("admin_password",
               default=None,
               help="The administrative user's password."),
    cfg.StrOpt("admin_auth_url",
               default=None,
               help="URL for where to find the OpenStack Identity admin "
                    "API endpoint."),
    cfg.BoolOpt("insecure",
                default=False,
                help="Disable SSL certificate verification."),
]

base_opts = [
    cfg.StrOpt("manila_exec_dir",
               default=os.environ.get(
                   'OS_MANILA_EXEC_DIR',
                   os.path.join(os.path.abspath('.'), '.tox/functional/bin')),
               help="The path to manilaclient to be executed."),
    cfg.BoolOpt("suppress_errors_in_cleanup",
                default=True,
                help="Whether to suppress errors with clean up operation "
                     "or not."),
]

share_opts = [
    cfg.StrOpt("min_api_microversion",
               default="1.0",
               help="The minimum API microversion is configured to be the "
                    "value of the minimum microversion supported by "
                    "Manilaclient functional tests. Defaults to 1.0."),
    cfg.StrOpt("max_api_microversion",
               default=api_versions.MAX_VERSION,
               help="The maximum API microversion is configured to be the "
                    "value of the latest microversion supported by "
                    "Manilaclient functional tests. Defaults to "
                    "manilaclient's max supported API microversion."),
    cfg.StrOpt("share_network",
               default=None,
               help="Share network Name or ID, that will be used for shares. "
                    "Some backend drivers require a share network for share "
                    "creation."),
    cfg.StrOpt("admin_share_network",
               default=None,
               help="Share network Name or ID, that will be used for shares "
                    "in admin tenant."),
    cfg.StrOpt("share_type",
               default=None,
               help="Share type Name or ID, that will be used with share "
                    "creation scheduling. Optional."),
    cfg.ListOpt("enable_protocols",
                default=["nfs", "cifs"],
                help="List of all enabled protocols. The first protocol in "
                     "the list will be used as the default protocol."),
    cfg.IntOpt("build_interval",
               default=3,
               help="Time in seconds between share availability checks."),
    cfg.IntOpt("build_timeout",
               default=500,
               help="Timeout in seconds to wait for a share to become "
                    "available."),
    cfg.DictOpt('access_types_mapping',
                default={'nfs': 'ip', 'cifs': 'ip'},
                help="Dict contains access types mapping to share "
                     "protocol. It will be used to create access rules "
                     "for shares. Format: '<protocol>: <type1> <type2>',..."
                     "Allowed share protocols: nfs, cifs, cephfs, glusterfs, "
                     "hdfs."),
    cfg.DictOpt('access_levels_mapping',
                default={'nfs': 'rw ro', 'cifs': 'rw'},
                help="Dict contains access levels mapping to share "
                     "protocol. It will be used to create access rules for "
                     "shares. Format: '<protocol>: <level1> <level2>',... "
                     "Allowed share protocols: nfs, cifs, cephfs, glusterfs, "
                     "hdfs."),
    cfg.StrOpt("username_for_user_rules",
               default="TESTDOMAIN\\Administrator",
               help="Username, that will be used in share access tests for "
                    "user type of access."),
]

# 2. Generate config

PROJECT_NAME = 'manilaclient'

DEFAULT_CONFIG_FILE = (
    os.environ.get('OS_%s_CONFIG_FILE' % PROJECT_NAME.upper()) or
    '%s.conf' % PROJECT_NAME)
DEFAULT_CONFIG_DIR = (
    os.environ.get('OS_%s_CONFIG_DIR' % PROJECT_NAME.upper()) or
    os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
                 "etc/manilaclient")
)
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE)
FAILOVER_CONFIG_PATH = '/etc/%(pn)s/%(cn)s' % {
    'pn': PROJECT_NAME, 'cn': DEFAULT_CONFIG_FILE}
CONFIG_FILES = []

if os.path.isfile(DEFAULT_CONFIG_PATH):
    CONFIG_FILES.append(DEFAULT_CONFIG_PATH)
if os.path.isfile(FAILOVER_CONFIG_PATH):
    CONFIG_FILES.append(FAILOVER_CONFIG_PATH)

CONF = cfg.CONF

if CONFIG_FILES:
    CONF([], project=PROJECT_NAME, default_config_files=CONFIG_FILES)
else:
    CONF([], project=PROJECT_NAME)

# 3. Register opts

CONF.register_opts(auth_opts)
CONF.register_opts(base_opts)
CONF.register_opts(share_opts)

# 4. Define list_opts for config sample generator


def list_opts():
    """Return a list of oslo_config options available in Manilaclient."""
    opts = [
        (None, copy.deepcopy(auth_opts)),
        (None, copy.deepcopy(base_opts)),
        (None, copy.deepcopy(share_opts)),
    ]
    opts.extend(log_options.list_opts())
    return opts
