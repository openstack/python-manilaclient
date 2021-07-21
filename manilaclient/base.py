# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
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
Base utilities to build API operation managers and objects on top of.
"""

import contextlib
import hashlib
import os

from manilaclient.common import cliutils
from manilaclient import exceptions
from manilaclient import utils


# Python 2.4 compat
try:
    all
except NameError:
    def all(iterable):
        return True not in (not x for x in iterable)


class Manager(utils.HookableMixin):
    """Manager for CRUD operations.

    Managers interact with a particular type of API (shares, snapshots,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api
        self.client = api.client

    @property
    def api_version(self):
        return self.api.api_version

    def _list(self, url, response_key, obj_class=None, body=None):
        resp = None
        if body:
            resp, body = self.api.client.post(url, body=body)
        else:
            resp, body = self.api.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        if isinstance(data, dict):
            try:
                data = data['values']
            except KeyError:
                pass

        with self.completion_cache('human_id', obj_class, mode="w"):
            with self.completion_cache('uuid', obj_class, mode="w"):
                resource = [obj_class(self, res, loaded=True)
                            for res in data if res]
                if 'count' in body:
                    return resource, body['count']
                else:
                    return resource

    @contextlib.contextmanager
    def completion_cache(self, cache_type, obj_class, mode):
        """Bash autocompletion items storage.

        The completion cache store items that can be used for bash
        autocompletion, like UUIDs or human-friendly IDs.

        A resource listing will clear and repopulate the cache.

        A resource create will append to the cache.

        Delete is not handled because listings are assumed to be performed
        often enough to keep the cache reasonably up-to-date.
        """
        base_dir = cliutils.env('manilaclient_UUID_CACHE_DIR',
                                'MANILACLIENT_UUID_CACHE_DIR',
                                default="~/.cache/manilaclient")

        # NOTE(sirp): Keep separate UUID caches for each username + endpoint
        # pair
        username = cliutils.env('OS_USERNAME', 'MANILA_USERNAME')
        url = cliutils.env('OS_URL', 'MANILA_URL')
        uniqifier = hashlib.sha1(username.encode('utf-8') +
                                 url.encode('utf-8')).hexdigest()

        cache_dir = os.path.expanduser(os.path.join(base_dir, uniqifier))

        try:
            os.makedirs(cache_dir, 0o755)
        except OSError:
            # NOTE(kiall): This is typically either permission denied while
            #              attempting to create the directory, or the directory
            #              already exists. Either way, don't fail.
            pass

        resource = obj_class.__name__.lower()
        filename = "%s-%s-cache" % (resource, cache_type.replace('_', '-'))
        path = os.path.join(cache_dir, filename)

        cache_attr = "_%s_cache" % cache_type

        try:
            setattr(self, cache_attr, open(path, mode))
        except IOError:
            # NOTE(kiall): This is typically a permission denied while
            #              attempting to write the cache file.
            pass

        try:
            yield
        finally:
            cache = getattr(self, cache_attr, None)
            if cache:
                cache.close()
                delattr(self, cache_attr)

    def write_to_completion_cache(self, cache_type, val):
        cache = getattr(self, "_%s_cache" % cache_type, None)
        if cache:
            try:
                cache.write("%s\n" % val)
            except UnicodeEncodeError:
                pass

    def _get(self, url, response_key=None):
        resp, body = self.api.client.get(url)
        if response_key:
            return self.resource_class(self, body[response_key], loaded=True)
        else:
            return self.resource_class(self, body, loaded=True)

    def _get_with_base_url(self, url, response_key=None):
        resp, body = self.api.client.get_with_base_url(url)
        if response_key:
            return [self.resource_class(self, res, loaded=True)
                    for res in body[response_key] if res]
        else:
            return self.resource_class(self, body, loaded=True)

    def _create(self, url, body, response_key, return_raw=False, **kwargs):
        self.run_hooks('modify_body_for_create', body, **kwargs)
        resp, body = self.api.client.post(url, body=body)
        if return_raw:
            return body[response_key]

        with self.completion_cache('human_id', self.resource_class, mode="a"):
            with self.completion_cache('uuid', self.resource_class, mode="a"):
                return self.resource_class(self, body[response_key])

    def _delete(self, url):
        resp, body = self.api.client.delete(url)

    def _update(self, url, body, response_key=None, **kwargs):
        self.run_hooks('modify_body_for_update', body, **kwargs)
        resp, body = self.api.client.put(url, body=body)
        if body:
            if response_key:
                return self.resource_class(self, body[response_key])
            else:
                return self.resource_class(self, body)

    def _build_query_string(self, search_opts):
        search_opts = search_opts or {}
        search_opts = utils.unicode_key_value_to_string(search_opts)
        params = sorted(
            [(k, v) for (k, v) in search_opts.items() if v])
        query_string = "?%s" % utils.safe_urlencode(params) if params else ''
        return query_string


class ManagerWithFind(Manager):
    """Like a `Manager`, but with additional `find()`/`findall()` methods."""
    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = list(kwargs.items())

        search_opts = {'all_tenants': 1}
        for obj in self.list(search_opts=search_opts):
            try:
                if all(getattr(obj, attr) == value
                       for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue

        return found

    def list(self, search_opts=None):
        raise NotImplementedError
