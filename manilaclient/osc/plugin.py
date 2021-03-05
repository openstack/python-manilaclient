# Copyright 2019 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.


"""OpenStackClient plugin for the Shared File System Service."""

import logging

from osc_lib import utils

from manilaclient import api_versions
from manilaclient.common import constants
from manilaclient import exceptions

LOG = logging.getLogger(__name__)

API_NAME = 'share'
API_VERSION_OPTION = 'os_share_api_version'
CLIENT_CLASS = 'manilaclient.v2.client.Client'
LATEST_VERSION = api_versions.MAX_VERSION
LATEST_MINOR_VERSION = api_versions.MAX_VERSION.split('.')[-1]


API_VERSIONS = {
    '2.%d' % i: CLIENT_CLASS
    for i in range(0, int(LATEST_MINOR_VERSION) + 1)
}


def _get_manila_url_from_service_catalog(instance):
    service_type = constants.SFS_SERVICE_TYPE
    url = instance.get_endpoint_for_service_type(
        constants.SFS_SERVICE_TYPE, region_name=instance._region_name,
        interface=instance.interface)
    # Fallback if cloud is using an older service type name
    if not url:
        url = instance.get_endpoint_for_service_type(
            constants.V2_SERVICE_TYPE, region_name=instance._region_name,
            interface=instance.interface)
        service_type = constants.V2_SERVICE_TYPE
    if url is None:
        raise exceptions.EndpointNotFound(
            message="Could not find manila / shared-file-system endpoint in "
                    "the service catalog.")
    return service_type, url


def make_client(instance):
    """Returns a shared file system service client."""
    requested_api_version = instance._api_version[API_NAME]

    shared_file_system_client = utils.get_client_class(
        API_NAME, requested_api_version, API_VERSIONS)

    # Cast the API version into an object for further processing
    requested_api_version = api_versions.APIVersion(
        version_str=requested_api_version)

    LOG.debug('Instantiating Shared File System (share) client: %s',
              shared_file_system_client)
    LOG.debug('Shared File System API version: %s',
              requested_api_version)

    service_type, manila_endpoint_url = _get_manila_url_from_service_catalog(
        instance)

    instance.setup_auth()
    debugging_enabled = instance._cli_options.debug
    client = shared_file_system_client(session=instance.session,
                                       service_catalog_url=manila_endpoint_url,
                                       endpoint_type=instance.interface,
                                       region_name=instance.region_name,
                                       service_type=service_type,
                                       auth=instance.auth,
                                       http_log_debug=debugging_enabled,
                                       api_version=requested_api_version,
                                       cert=instance.cert)
    return client


def build_option_parser(parser):
    """Hook to add global options."""
    default_api_version = utils.env('OS_SHARE_API_VERSION') or LATEST_VERSION
    parser.add_argument(
        '--os-share-api-version',
        metavar='<shared-file-system-api-version>',
        default=default_api_version,
        choices=sorted(
            API_VERSIONS,
            key=lambda k: [int(x) for x in k.split('.')]),
        help='Shared File System API version, default=' + default_api_version +
             'version supported by both the client and the server). '
             '(Env: OS_SHARE_API_VERSION)',
    )
    return parser
