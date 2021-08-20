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
        self.share_groups = mock.Mock()
        self.share_types = mock.Mock()
        self.share_type_access = mock.Mock()
        self.quotas = mock.Mock()
        self.quota_classes = mock.Mock()
        self.share_snapshots = mock.Mock()
        self.share_snapshot_export_locations = mock.Mock()
        self.share_snapshot_instances = mock.Mock()
        self.share_replicas = mock.Mock()
        self.share_replica_export_locations = mock.Mock()
        self.share_networks = mock.Mock()
        self.share_network_subnets = mock.Mock()
        self.security_services = mock.Mock()
        self.shares.resource_class = osc_fakes.FakeResource(None, {})
        self.share_instance_export_locations = mock.Mock()
        self.share_export_locations = mock.Mock()
        self.share_snapshot_instance_export_locations = mock.Mock()
        self.share_export_locations.resource_class = (
            osc_fakes.FakeResource(None, {}))
        self.messages = mock.Mock()
        self.availability_zones = mock.Mock()
        self.services = mock.Mock()
        self.share_instances = mock.Mock()
        self.pools = mock.Mock()
        self.limits = mock.Mock()
        self.share_group_types = mock.Mock()
        self.share_group_type_access = mock.Mock()


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
            "scheduler_hints": {},
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
            "id": "id-" + uuid.uuid4().hex,
            "is_admin_only": False,
            "preferred": False,
            "updated_at": 'time-' + uuid.uuid4().hex,
        }

        share_export_location_info.update(attrs)
        share_export_location = osc_fakes.FakeResource(info=copy.deepcopy(
            share_export_location_info),
            loaded=True)
        return share_export_location

    @staticmethod
    def create_share_export_locations(attrs=None, count=2):
        """Create multiple fake export locations.

        :param Dictionary attrs:
            A dictionary with all attributes

        :param Integer count:
            The number of share export locations to be faked

        :return:
            A list of FakeResource objects
        """

        share_export_locations = []
        for n in range(0, count):
            share_export_locations.append(
                FakeShareExportLocation.
                create_one_export_location(attrs))
        return share_export_locations


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
            'state': 'active',
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
            'snapshots': 50,
            'per_share_gigabytes': -1,
        }

        quotas_info.update(attrs)
        quotas = osc_fakes.FakeResource(info=copy.deepcopy(
                                        quotas_info),
                                        loaded=True)
        return quotas


class FakeShareSnapshotIntances(object):
    """Fake a share snapshot instance"""

    @staticmethod
    def create_one_snapshot_instance(attrs=None, methods=None):
        """Create a fake share snapshot instance

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}
        share_snapshot_instance = {
            'id': 'snapshot-instance-id-' + uuid.uuid4().hex,
            'snapshot_id': 'snapshot-id-' + uuid.uuid4().hex,
            'status': None,
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'share_id': 'share-id-' + uuid.uuid4().hex,
            'share_instance_id': 'share-instance-id-' + uuid.uuid4().hex,
            'progress': None,
            'provider_location': None
        }

        share_snapshot_instance.update(attrs)
        share_snapshot_instance = osc_fakes.FakeResource(info=copy.deepcopy(
            share_snapshot_instance),
            methods=methods,
            loaded=True)
        return share_snapshot_instance

    @staticmethod
    def create_share_snapshot_instances(attrs=None, count=2):
        """Create multiple fake snapshot instances.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share snapshot instances to be faked
        :return:
            A list of FakeResource objects
        """

        share_snapshot_instances = []
        for n in range(0, count):
            share_snapshot_instances.append(
                FakeShareSnapshot.create_one_snapshot(attrs))

        return share_snapshot_instances


class FakeShareSnapshotInstancesExportLocations(object):
    """Fake a share snapshot instance Export Locations"""

    @staticmethod
    def create_one_snapshot_instance(attrs=None, methods=None):
        """Create a fake share snapshot instance export locations

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}
        share_snapshot_instance_export_location = {
            'id': 'snapshot-instance-export-location-id-' + uuid.uuid4().hex,
            'is_admin_only': False,
            'path': '0.0.0.0/:fake-share-instance-export-location-id',
        }

        share_snapshot_instance_export_location.update(attrs)
        share_snapshot_instance_export_location = osc_fakes.FakeResource(
            info=copy.deepcopy(
                share_snapshot_instance_export_location),
            methods=methods,
            loaded=True)
        return share_snapshot_instance_export_location

    @staticmethod
    def create_share_snapshot_instances(attrs=None, count=2):
        """Create multiple fake snapshot instances.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share snapshot instance locations to be faked
        :return:
            A list of FakeResource objects
        """

        share_snapshot_instances = []
        for n in range(0, count):
            share_snapshot_instances.append(
                FakeShareSnapshot.create_one_snapshot(attrs))

        return share_snapshot_instances


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


class FakeShareReplica(object):
    """Fake a share replica"""

    @staticmethod
    def create_one_replica(attrs=None, methods=None):
        """Create a fake share replica

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

        share_replica = {
            'availability_zone': None,
            'cast_rules_to_readonly': True,
            'created_at': datetime.datetime.now().isoformat(),
            'host': None,
            'id': 'replica-id-' + uuid.uuid4().hex,
            'replica_state': None,
            'share_id': 'share-id-' + uuid.uuid4().hex,
            'share_network_id': None,
            'share_server_id': None,
            'status': None,
            'updated_at': None
        }

        share_replica.update(attrs)
        share_replica = osc_fakes.FakeResource(info=copy.deepcopy(
            share_replica),
            methods=methods,
            loaded=True)
        return share_replica

    @staticmethod
    def create_share_replicas(attrs=None, count=2):
        """Create multiple fake replicas.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share types to be faked
        :return:
            A list of FakeResource objects
        """

        share_replicas = []
        for n in range(0, count):
            share_replicas.append(
                FakeShareReplica.create_one_replica(attrs))
        return share_replicas


class FakeShareAvailabilityZones(object):
    """Fake one or more availability zones"""

    @staticmethod
    def create_one_availability_zone(attrs=None):
        """Create a fake share availability zone

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        availability_zone = {
            "id": 'id-' + uuid.uuid4().hex,
            "name": 'name-' + uuid.uuid4().hex,
            "created_at": 'time-' + uuid.uuid4().hex,
            "updated_at": 'time-' + uuid.uuid4().hex,
        }

        availability_zone.update(attrs)
        availability_zone = osc_fakes.FakeResource(info=copy.deepcopy(
            availability_zone),
            loaded=True)
        return availability_zone

    @staticmethod
    def create_share_availability_zones(attrs=None, count=2):

        """Create multiple availability zones.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of availability zones to be faked
        :return:
            A list of FakeResource objects
        """

        availability_zones = []
        for n in range(0, count):
            availability_zones.append(
                FakeShareAvailabilityZones.create_one_availability_zone(attrs))
        return availability_zones


class FakeShareService(object):
    """Fake one or more share service"""

    @staticmethod
    def create_fake_service(attrs=None):
        """Create a fake share service

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        share_service_info = {
            "binary": "manila-share",
            "host": "fake_host@fake_backend",
            "id": uuid.uuid4().hex,
            "status": "enabled",
            "state": "up",
            "updated_at": 'time-' + uuid.uuid4().hex,
            "zone": "fake_zone"
        }

        share_service_info.update(attrs)
        share_service = osc_fakes.FakeResource(info=copy.deepcopy(
            share_service_info),
            loaded=True)
        return share_service

    @staticmethod
    def create_fake_services(attrs=None, count=2):
        """Create multiple fake services.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share services to be faked
        :return:
            A list of FakeResource objects
        """

        services = []
        for n in range(count):
            services.append(
                FakeShareService.create_fake_service(attrs))
        return services


class FakeSharePools(object):
    """Fake one or more share pool"""

    @staticmethod
    def create_one_share_pool(attrs=None):
        """Create a fake share pool

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object
        """

        attrs = attrs or {}

        share_pool = {
            "name": 'fake_pool@gamma#fake_pool',
            "host": 'fake_host_' + uuid.uuid4().hex,
            "backend": 'fake_backend_' + uuid.uuid4().hex,
            "pool": 'fake_pool_' + uuid.uuid4().hex,
            "capabilities": {'fake_capability': uuid.uuid4().hex}
        }

        share_pool.update(attrs)
        share_pool = osc_fakes.FakeResource(info=copy.deepcopy(
            share_pool),
            loaded=True)
        return share_pool

    @staticmethod
    def create_share_pools(attrs=None, count=2):
        """Create multiple fake share pools.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share pools to be faked
        :return:
            A list of FakeResource objects
        """

        share_pools = []
        for n in range(count):
            share_pools.append(
                FakeSharePools.create_one_share_pool(attrs))
        return share_pools


class FakeShareInstance(object):
    """Fake a share instance"""

    @staticmethod
    def create_one_share_instance(attrs=None, methods=None):
        """Create a fake share instance

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """
        attrs = attrs or {}
        methods = methods or {}

        share_instance = {
            'status': None,
            'progress': None,
            'share_id': 'share-id-' + uuid.uuid4().hex,
            'availability_zone': None,
            'replica_state': None,
            'created_at': datetime.datetime.now().isoformat(),
            'cast_rules_to_readonly': False,
            'share_network_id': 'sn-id-' + uuid.uuid4().hex,
            'share_server_id': 'ss-id-' + uuid.uuid4().hex,
            'host': None,
            'access_rules_status': None,
            'id': 'instance-id-' + uuid.uuid4().hex
        }

        share_instance.update(attrs)
        share_instance = osc_fakes.FakeResource(info=copy.deepcopy(
            share_instance),
            methods=methods,
            loaded=True)
        return share_instance

    @staticmethod
    def create_share_instances(attrs=None, count=2):
        """Create multiple fake instances.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share instances to be faked
        :return:
            A list of FakeResource objects
        """
        share_instances = []
        for n in range(count):
            share_instances.append(
                FakeShareInstance.create_one_share_instance(attrs))
        return share_instances


class FakeShareLimits(object):
    """Fake one or more share limits"""

    @staticmethod
    def create_one_share_limit(attrs=None):
        """Create a fake share limit dict

         :param Dictionary attrs:
             A dictionary with all attributes
         :return:
             A FakeLimitsResource object, with share limits.
         """

        attrs = attrs or {}

        share_limits = {
            'absolute_limit': {
                "totalShareNetworksUsed": 4,
            },
            'rate_limit': {
                "regex": "^/shares",
                "uri": "/shares",
                "verb": "GET",
                "next-available": "2021-09-01T00:00:00Z",
                "unit": "MINUTE",
                "value": "3",
                "remaining": "1",
            }
        }

        share_limits.update(attrs)
        share_limits = osc_fakes.FakeLimitsResource(
            info=copy.deepcopy(share_limits), loaded=True)
        return share_limits


class FakeShareNetwork(object):
    """Fake a share network"""

    @staticmethod
    def create_one_share_network(attrs=None, methods=None):
        """Create a fake share network

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

        share_network = {
            'id': str(uuid.uuid4()),
            'project_id': uuid.uuid4().hex,
            'created_at': datetime.datetime.now().isoformat(),
            'description': 'description-' + uuid.uuid4().hex,
            'name': 'name-' + uuid.uuid4().hex,
            "status": "active",
            "security_service_update_support": True,
            'share_network_subnets': [
                {
                    'id': str(uuid.uuid4()),
                    "availability_zone": None,
                    "created_at": datetime.datetime.now().isoformat(),
                    "updated_at": datetime.datetime.now().isoformat(),
                    "segmentation_id": 1010,
                    "neutron_net_id": str(uuid.uuid4()),
                    "neutron_subnet_id": str(uuid.uuid4()),
                    "ip_version": 4,
                    "cidr": "10.0.0.0/24",
                    "network_type": "vlan",
                    "mtu": "1500",
                    "gateway": "10.0.0.1"
                },
            ],
        }

        share_network.update(attrs)
        share_network = osc_fakes.FakeResource(info=copy.deepcopy(
            share_network),
            methods=methods,
            loaded=True)
        return share_network

    @staticmethod
    def create_share_networks(attrs=None, count=2):
        """Create multiple fake share networks.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share networks to be faked

        :return:
            A list of FakeResource objects
        """

        share_networks = []
        for n in range(count):
            share_networks.append(
                FakeShareNetwork.create_one_share_network(attrs))

        return share_networks


class FakeShareNetworkSubnet(object):
    """Fake a share network subnet"""

    @staticmethod
    def create_one_share_subnet(attrs=None):
        """Create a fake share network subnet

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}

        share_network_subnet = {
            "availability_zone": None,
            "cidr": "10.0.0.0/24",
            "created_at": datetime.datetime.now().isoformat(),
            "gateway": "10.0.0.1",
            'id': str(uuid.uuid4()),
            "ip_version": 4,
            "mtu": "1500",
            "network_type": "vlan",
            "neutron_net_id": str(uuid.uuid4()),
            "neutron_subnet_id": str(uuid.uuid4()),
            "segmentation_id": 1010,
            "share_network_id": str(uuid.uuid4()),
            "share_network_name": str(uuid.uuid4()),
            "updated_at": datetime.datetime.now().isoformat(),
        }

        share_network_subnet.update(attrs)
        share_network_subnet = osc_fakes.FakeResource(info=copy.deepcopy(
            share_network_subnet),
            loaded=True)
        return share_network_subnet

    @staticmethod
    def create_share_network_subnets(attrs=None, count=2):
        """Create multiple fake share network subnets.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share network subnets to be faked
        :return:
            A list of FakeResource objects
        """

        share_network_subnets = []
        for n in range(count):
            share_network_subnets.append(
                FakeShareNetworkSubnet.create_one_share_subnet(attrs))

        return share_network_subnets


class FakeShareGroup(object):
    """Fake a share group"""

    @staticmethod
    def create_one_share_group(attrs=None, methods=None):
        """Create a fake share group

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

        share_group = {
            "id": 'share-group-id-' + uuid.uuid4().hex,
            'name': None,
            'created_at': datetime.datetime.now().isoformat(),
            'status': 'available',
            'description': None,
            'availability_zone': None,
            "project_id": 'project-id-' + uuid.uuid4().hex,
            'host': None,
            'share_group_type_id': 'share-group-type-id-' + uuid.uuid4().hex,
            'source_share_group_snapshot_id': None,
            'share_network_id': None,
            'share_server_id': None,
            'share_types': ['share-types-id-' + uuid.uuid4().hex],
            'consistent_snapshot_support': None
        }

        share_group.update(attrs)
        share_group = osc_fakes.FakeResource(info=copy.deepcopy(
            share_group),
            methods=methods,
            loaded=True)
        return share_group

    @staticmethod
    def create_share_groups(attrs=None, count=2):
        """Create multiple fake groups.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share groups to be faked
        :return:
            A list of FakeResource objects
        """

        share_groups = []
        for n in range(0, count):
            share_groups.append(
                FakeShareGroup.create_one_share_group(attrs))
        return share_groups


class FakeShareGroupType(object):
    """Fake one or more share group types"""

    @staticmethod
    def create_one_share_group_type(attrs=None, methods=None):
        """Create a fake share group type

        :param Dictionary attrs:
            A dictionary with all attributes
        :return:
            A FakeResource object, with project_id, resource and so on
        """

        attrs = attrs or {}
        methods = methods or {}

        share_group_type_info = {
            "is_public": True,
            "group_specs": {
                "snapshot_support": True
            },
            "share_types": ['share-types-id-' + uuid.uuid4().hex],
            "id": 'share-group-type-id-' + uuid.uuid4().hex,
            "name": 'share-group-type-name-' + uuid.uuid4().hex,
            "is_default": False
        }

        share_group_type_info.update(attrs)
        share_group_type = osc_fakes.FakeResource(info=copy.deepcopy(
                                                  share_group_type_info),
                                                  methods=methods,
                                                  loaded=True)
        return share_group_type

    @staticmethod
    def create_share_group_types(attrs=None, count=2):
        """Create multiple fake share group types.

        :param Dictionary attrs:
            A dictionary with all attributes
        :param Integer count:
            The number of share group types to be faked
        :return:
            A list of FakeResource objects
        """

        share_group_types = []
        for n in range(0, count):
            share_group_types.append(
                FakeShareGroupType.create_one_share_group_type(attrs))

        return share_group_types

    @staticmethod
    def get_share_group_types(share_group_types=None, count=2):
        """Get an iterable MagicMock object with a list of faked group types.

        If types list is provided, then initialize the Mock object with the
        list. Otherwise create one.

        :param List types:
            A list of FakeResource objects faking types
        :param Integer count:
            The number of group types to be faked
        :return
            An iterable Mock object with side_effect set to a list of faked
            group types
        """

        if share_group_types is None:
            share_group_types = FakeShareGroupType.share_group_types(count)

        return mock.Mock(side_effect=share_group_types)
