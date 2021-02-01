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
import datetime
import random
from unittest import mock
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
        self.share_access_rules = mock.Mock()
        self.share_types = mock.Mock()
        self.share_type_access = mock.Mock()
        self.quotas = mock.Mock()
        self.share_snapshots = mock.Mock()
        self.share_snapshot_export_locations = mock.Mock()
        self.shares.resource_class = osc_fakes.FakeResource(None, {})
        self.share_export_locations = mock.Mock()
        self.share_export_locations.resource_class = (
            osc_fakes.FakeResource(None, {}))
        self.messages = mock.Mock()


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
    def create_one_share(attrs=None, methods=None):
        """Create a fake share.

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with flavor_id, image_id, and so on
        """

        attrs = attrs or {}
        methods = methods or {}

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
                                       methods=methods,
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
    def create_one_sharetype(attrs=None, methods=None):
        """Create a fake share type

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

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
                                            methods=methods,
                                            loaded=True)
        return share_type

    @staticmethod
    def create_share_types(attrs=None, count=2):
        """Create multiple fake share types.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        share_types = []
        for n in range(0, count):
            share_types.append(FakeShareType.create_one_sharetype(attrs))

        return share_types

    @staticmethod
    def get_share_types(share_types=None, count=2):
        """Get an iterable MagicMock object with a list of faked types.

        If types list is provided, then initialize the Mock object with the
        list. Otherwise create one.

        :param List types:
            A list of FakeResource objects faking types
        :param Integer count:
            The number of types to be faked
        :return
            An iterable Mock object with side_effect set to a list of faked
            types
        """

        if share_types is None:
            share_types = FakeShareType.create_share_types(count)

        return mock.Mock(side_effect=share_types)


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
            "created_at": 'time-' + uuid.uuid4().hex,
            "fake_path": "/foo/el/path",
            "fake_share_instance_id": 'share-instance-id' + uuid.uuid4().hex,
            "fake_uuid": "foo_el_uuid",
            "is_admin_only": False,
            "preferred": False,
            "updated_at": 'time-' + uuid.uuid4().hex,
        }

        share_export_location_info.update(attrs)
        share_export_location = osc_fakes.FakeResource(info=copy.deepcopy(
            share_export_location_info),
            loaded=True)
        return share_export_location


class FakeShareAccessRule(object):
    """Fake one or more share access rules"""

    @staticmethod
    def create_one_access_rule(attrs=None):
        """Create a fake share access rule

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        share_access_rule = {
            'id': 'access_rule-id-' + uuid.uuid4().hex,
            'share_id': 'share-id-' + uuid.uuid4().hex,
            'access_level': 'rw',
            'access_to': 'demo',
            'access_type': 'user',
            'state': 'queued_to_apply',
            'access_key': None,
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': None,
            'properties': {}
        }

        share_access_rule.update(attrs)
        share_access_rule = osc_fakes.FakeResource(info=copy.deepcopy(
            share_access_rule),
            loaded=True)
        return share_access_rule


class FakeQuotaSet(object):
    """Fake quota set"""

    @staticmethod
    def create_fake_quotas(attrs=None):
        """Create a fake quota set

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        quotas_info = {
            'gigabytes': 1000,
            'id': 'tenant-id-c96a43119a40ec7d01794cb8',
            'share_group_snapshots': 50,
            'share_groups': 50,
            'share_networks': 10,
            'shares': 50,
            'shapshot_gigabytes': 1000,
            'snapshots': 50
        }

        quotas_info.update(attrs)
        quotas = osc_fakes.FakeResource(info=copy.deepcopy(
                                        quotas_info),
                                        loaded=True)
        return quotas


class FakeShareSnapshot(object):
    """Fake a share snapshot"""

    @staticmethod
    def create_one_snapshot(attrs=None, methods=None):
        """Create a fake share snapshot

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

        share_snapshot = {
            'created_at': datetime.datetime.now().isoformat(),
            'description': 'description-' + uuid.uuid4().hex,
            'id': 'snapshot-id-' + uuid.uuid4().hex,
            'name': 'name-' + uuid.uuid4().hex,
            'project_id': 'project-id-' + uuid.uuid4().hex,
            'provider_location': None,
            'share_id': 'share-id-' + uuid.uuid4().hex,
            'share_proto': 'NFS',
            'share_size': 1,
            'size': 1,
            'status': None,
            'user_id': 'user-id-' + uuid.uuid4().hex
        }

        share_snapshot.update(attrs)
        share_snapshot = osc_fakes.FakeResource(info=copy.deepcopy(
            share_snapshot),
            methods=methods,
            loaded=True)
        return share_snapshot

    @staticmethod
    def create_share_snapshots(attrs=None, count=2):
        """Create multiple fake snapshots.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        share_snapshots = []
        for n in range(0, count):
            share_snapshots.append(
                FakeShareSnapshot.create_one_snapshot(attrs))

        return share_snapshots


class FakeSnapshotAccessRule(object):
    """Fake one or more snapshot access rules"""

    @staticmethod
    def create_one_access_rule(attrs={}):
        """Create a fake snapshot access rule

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        snapshot_access_rule = {
            'access_to': 'demo',
            'access_type': 'user',
            'id': 'access_rule-id-' + uuid.uuid4().hex,
            'state': 'queued_to_apply'
        }

        snapshot_access_rule.update(attrs)
        snapshot_access_rule = osc_fakes.FakeResource(info=copy.deepcopy(
            snapshot_access_rule),
            loaded=True)
        return snapshot_access_rule

    @staticmethod
    def create_access_rules(attrs={}, count=2):
        """Create multiple fake snapshots.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        access_rules = []
        for n in range(0, count):
            access_rules.append(
                FakeSnapshotAccessRule.create_one_access_rule(attrs))

        return access_rules


class FakeSnapshotExportLocation(object):
    """Fake one or more export locations"""

    @staticmethod
    def create_one_export_location(attrs=None):
        """Create a fake snapshot export location

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        snapshot_export_location_info = {
            "created_at": 'time-' + uuid.uuid4().hex,
            "id": "id-" + uuid.uuid4().hex,
            "is_admin_only": False,
            "links": [],
            "path": "/path/to/fake/snapshot/snapshot",
            "share_snapshot_instance_id": 'instance-id' + uuid.uuid4().hex,
            "updated_at": 'time-' + uuid.uuid4().hex,
        }

        snapshot_export_location_info.update(attrs)
        snapshot_export_location = osc_fakes.FakeResource(info=copy.deepcopy(
            snapshot_export_location_info),
            loaded=True)
        return snapshot_export_location

    @staticmethod
    def create_export_locations(attrs={}, count=2):
        """Create multiple fake export locations.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        export_locations = []
        for n in range(0, count):
            export_locations.append(
                FakeSnapshotExportLocation.create_one_export_location(
                    attrs))

        return export_locations


class FakeMessage(object):
    """Fake message"""

    @staticmethod
    def create_one_message(attrs=None):
        """Create a fake message

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        message = {
            'id': 'message-id-' + uuid.uuid4().hex,
            'action_id': '001',
            'detail_id': '002',
            'user_message': 'user message',
            'message_level': 'ERROR',
            'resource_type': 'SHARE',
            'resource_id': 'resource-id-' + uuid.uuid4().hex,
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': (
                datetime.datetime.now() + datetime.timedelta(days=30)
            ).isoformat(),
            'request_id': 'req-' + uuid.uuid4().hex,
        }

        message.update(attrs)
        message = osc_fakes.FakeResource(info=copy.deepcopy(
            message),
            loaded=True)
        return message

    @staticmethod
    def create_messages(attrs={}, count=2):
        """Create multiple fake messages.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        messages = []
        for n in range(0, count):
            messages.append(
                FakeMessage.create_one_message(attrs))

        return messages
