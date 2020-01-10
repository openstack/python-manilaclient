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
#

import copy
import mock
import random
import uuid

from openstackclient.tests.unit.identity.v3 import fakes as identity_fakes

from manilaclient.tests.unit.osc import osc_fakes
from manilaclient.tests.unit.osc import osc_utils


class FakeShareClient(object):

    def __init__(self, **kwargs):
        super(FakeShareClient, self).__init__()
        self.auth_token = kwargs['token']
        self.management_url = kwargs['endpoint']
        self.shares = mock.Mock()
        self.shares.resource_class = osc_fakes.FakeResource(None, {})
        self.share_export_locations = mock.Mock()
        self.share_export_locations.resource_class = (
            osc_fakes.FakeResource(None, {}))


class ManilaParseException(Exception):
    """The base exception class for all exceptions this library raises."""

    def __init__(self, message=None, details=None):
        self.message = message or "Argument parse exception"
        self.details = details or None

    def __str__(self):
        return self.message


class TestShare(osc_utils.TestCommand):

    def setUp(self):
        super(TestShare, self).setUp()

        self.app.client_manager.share = FakeShareClient(
            endpoint=osc_fakes.AUTH_URL,
            token=osc_fakes.AUTH_TOKEN
        )

        self.app.client_manager.identity = identity_fakes.FakeIdentityv3Client(
            endpoint=osc_fakes.AUTH_URL,
            token=osc_fakes.AUTH_TOKEN
        )


class FakeShare(object):
    """Fake one or more shares."""

    @staticmethod
    def create_one_share(attrs=None):
        """Create a fake share.

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with flavor_id, image_id, and so on
        """

        attrs = attrs or {}

        # set default attributes.
        share_info = {
            "status": None,
            "share_server_id": None,
            "project_id": 'project-id-' + uuid.uuid4().hex,
            "name": 'share-name-' + uuid.uuid4().hex,
            "share_type": 'share-type-' + uuid.uuid4().hex,
            "share_type_name": "default",
            "availability_zone": None,
            "created_at": 'time-' + uuid.uuid4().hex,
            "share_network_id": None,
            "share_group_id": None,
            "share_proto": "NFS",
            "host": None,
            "access_rules_status": "active",
            "has_replicas": False,
            "replication_type": None,
            "task_state": None,
            "snapshot_support": True,
            "snapshot_id": None,
            "is_public": True,
            "metadata": {},
            "id": 'share-id-' + uuid.uuid4().hex,
            "size": random.randint(1, 20),
            "description": 'share-description-' + uuid.uuid4().hex,
            "user_id": 'share-user-id-' + uuid.uuid4().hex,
            "create_share_from_snapshot_support": False,
            "mount_snapshot_support": False,
            "revert_to_snapshot_support": False,
            "source_share_group_snapshot_member_id": None,
        }

        # Overwrite default attributes.
        share_info.update(attrs)

        share = osc_fakes.FakeResource(info=copy.deepcopy(share_info),
                                       loaded=True)
        return share

    @staticmethod
    def create_shares(attrs=None, count=2):
        """Create multiple fake shares.

        :param Dictionary attrs:
            A dictionary with all share attributes
        :param Integer count:
            The number of shares to be faked
        :return:
            A list of FakeResource objects
        """
        shares = []
        for n in range(0, count):
            shares.append(FakeShare.create_one_share(attrs))

        return shares

    @staticmethod
    def get_shares(shares=None, count=2):
        """Get an iterable MagicMock object with a list of faked shares.

        If a shares list is provided, then initialize the Mock object with the
        list. Otherwise create one.
        :param List shares:
            A list of FakeResource objects faking shares
        :param Integer count:
            The number of shares to be faked
        :return
            An iterable Mock object with side_effect set to a list of faked
            shares
        """
        if shares is None:
            shares = FakeShare.create_shares(count)

        return mock.Mock(side_effect=shares)

    @staticmethod
    def get_share_columns(share=None):
        """Get the shares columns from a faked shares object.

        :param shares:
            A FakeResource objects faking shares
        :return
            A tuple which may include the following keys:
            ('id', 'name', 'description', 'status', 'size', 'share_type',
             'metadata', 'snapshot', 'availability_zone')
        """
        if share is not None:
            return tuple(k for k in sorted(share.keys()))
        return tuple([])

    @staticmethod
    def get_share_data(share=None):
        """Get the shares data from a faked shares object.

        :param shares:
            A FakeResource objects faking shares
        :return
            A tuple which may include the following values:
            ('ce26708d', 'fake name', 'fake description', 'available',
             20, 'fake share type', "Manila='zorilla', Zorilla='manila',
             Zorilla='zorilla'", 1, 'nova')
        """
        data_list = []
        if share is not None:
            for x in sorted(share.keys()):
                if x == 'tags':
                    # The 'tags' should be format_list
                    data_list.append(
                        format_columns.ListColumn(share.info.get(x)))
                else:
                    data_list.append(share.info.get(x))
        return tuple(data_list)


class FakeShareType(object):
    """Fake one or more share types"""

    @staticmethod
    def create_one_sharetype(attrs=None):
        """Create a fake share type

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        share_type_info = {
            "required_extra_specs": {
                "driver_handles_share_servers": True
            },
            "share_type_access:is_public": True,
            "extra_specs": {
                "replication_type": "readable",
                "driver_handles_share_servers": True,
                "mount_snapshot_support": False,
                "revert_to_snapshot_support": False,
                "create_share_from_snapshot_support": True,
                "snapshot_support": True
            },
            "id": 'share-type-id-' + uuid.uuid4().hex,
            "name": 'share-type-name-' + uuid.uuid4().hex,
            "is_default": False,
            "description": 'share-type-description-' + uuid.uuid4().hex
        }

        share_type_info.update(attrs)
        share_type = osc_fakes.FakeResource(info=copy.deepcopy(
                                            share_type_info),
                                            loaded=True)
        return share_type


class FakeShareExportLocation(object):
    """Fake one or more export locations"""

    @staticmethod
    def create_one_export_location(attrs=None):
        """Create a fake share export location

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        share_export_location_info = {
            "fake_uuid": "foo_el_uuid",
            "fake_path": "/foo/el/path",
            "fake_share_instance_id": 'share-instance-id' + uuid.uuid4().hex,
            "is_admin_only": False,
            "created_at": 'time-' + uuid.uuid4().hex,
            "updated_at": 'time-' + uuid.uuid4().hex,
        }

        share_export_location_info.update(attrs)
        share_export_location = osc_fakes.FakeResource(info=copy.deepcopy(
            share_export_location_info),
            loaded=True)
        return share_export_location
