# Copyright (c) 2015 Clinton Knight.  All rights reserved.
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

from manilaclient import base

RESOURCES_PATH = '/scheduler-stats/pools'
RESOURCES_NAME = 'pools'


class Pool(base.Resource):
    def __repr__(self):
        return f"<Pool: {self.name}>"


class PoolManager(base.Manager):
    """Manage :class:`Pool` resources."""

    resource_class = Pool

    def list(self, detailed=True, search_opts=None):
        """Get a list of pools.

        :rtype: list of :class:`Pool`
        """
        query_string = self._build_query_string(search_opts)
        if detailed:
            path = f'{RESOURCES_PATH}/detail{query_string}'
        else:
            path = f'{RESOURCES_PATH}{query_string}'

        return self._list(path, RESOURCES_NAME)
