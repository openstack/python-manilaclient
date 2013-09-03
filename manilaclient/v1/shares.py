# Copyright 2012 NetApp
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
"""Interface for shares extention."""

import collections
import os
import re
import urllib

from cinderclient import base
from cinderclient import exceptions
from cinderclient import utils


class Share(base.Resource):
    """A share is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        return "<Share: %s>" % self.id

    def delete(self):
        """Delete this share."""
        self.manager.delete(self)

    def allow(self, access_type, access):
        """Allow access to a share."""
        self._validate_access(access_type, access)
        return self.manager.allow(self, access_type, access)

    def deny(self, id):
        """Deny access from IP to a share."""
        return self.manager.deny(self, id)

    def access_list(self):
        """Deny access from IP to a share."""
        return self.manager.access_list(self)

    def _validate_access(self, access_type, access):
        if access_type == 'ip':
            self._validate_ip_range(access)
        elif access_type == 'passwd':
            self._validate_username(access)
        else:
            raise exceptions.CommandError(
                'Only ip and passwd type are supported')

    @staticmethod
    def _validate_username(access):
        valid_useraname_re = '\w{4,32}'
        username = access
        if not re.match(valid_useraname_re, username):
            exc_str = _('Invalid user name. Must be alphanum 4-32 chars long')
            raise exceptions.CommandError(exc_str)

    @staticmethod
    def _validate_ip_range(ip_range):
        ip_range = ip_range.split('/')
        exc_str = ('Supported ip format examples:\n'
                   '\t10.0.0.2, 10.0.0.*, 10.0.0.0/24')
        if len(ip_range) > 2:
            raise exceptions.CommandError(exc_str)
        allow_asterisk = (len(ip_range) == 1)
        ip_range = ip_range[0].split('.')
        if len(ip_range) != 4:
            raise exceptions.CommandError(exc_str)
        for item in ip_range:
            try:
                if 0 <= int(item) <= 255:
                    continue
                raise ValueError()
            except ValueError:
                if not (allow_asterisk and item == '*'):
                    raise exceptions.CommandError(exc_str)


class ShareManager(base.ManagerWithFind):
    """Manage :class:`Share` resources."""
    resource_class = Share

    def create(self, share_proto, size, snapshot_id=None, name=None,
               description=None):
        """Create NAS.

        :param size: Size of NAS in GB
        :param snapshot_id: ID of the snapshot
        :param name: Name of the NAS
        :param description: Short description of a share
        :param share_proto: Type of NAS (NFS or CIFS)
        :rtype: :class:`Share`
        """
        body = {'share': {'size': size,
                          'snapshot_id': snapshot_id,
                          'name': name,
                          'description': description,
                          'share_proto': share_proto}}
        return self._create('/shares', body, 'share')

    def get(self, share_id):
        """Get a share.

        :param share_id: The ID of the share to delete.
        :rtype: :class:`Share`
        """
        return self._get("/shares/%s" % share_id, "share")

    def list(self, detailed=True, search_opts=None):
        """Get a list of all shares.

        :rtype: list of :class:`Share`
        """
        if search_opts:
            query_string = urllib.urlencode([(key, value)
                                             for (key, value)
                                             in search_opts.items()
                                             if value])
            if query_string:
                query_string = "?%s" % (query_string,)
        else:
            query_string = ''

        if detailed:
            path = "/shares/detail%s" % (query_string,)
        else:
            path = "/shares%s" % (query_string,)

        return self._list(path, 'shares')

    def delete(self, share):
        """Delete a share.

        :param share: The :class:`Share` to delete.
        """
        self._delete("/shares/%s" % base.getid(share))

    def allow(self, share, access_type, access):
        """Allow access from IP to a shares.

        :param share: The :class:`Share` to delete.
        :param access_type: string that represents access type ('ip','domain')
        :param access: string that represents access ('127.0.0.1')
        """
        return self._action('os-allow_access', share,
                            {'access_type': access_type,
                             'access_to': access})

    def deny(self, share, id):
        """Deny access from IP to a shares.

        :param share: The :class:`Share` to delete.
        :param ip: string that represents ip address
        """
        return self._action('os-deny_access', share, {'access_id': id})

    def access_list(self, share):
        """Get access list to the share."""
        access_list = self._action("os-access_list", share)[1]["access_list"]
        if access_list:
            t = collections.namedtuple('Access', access_list[0].keys())
            return [t(*value.values()) for value in access_list]
        else:
            return []

    def _action(self, action, share, info=None, **kwargs):
        """Perform a share 'action'."""
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/shares/%s/action' % base.getid(share)
        return self.api.client.post(url, body=body)


#########################
