# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import six


class HookableMixin(object):
    """Mixin so classes can register and run hooks."""
    _hooks_map = {}

    @classmethod
    def add_hook(cls, hook_type, hook_func):
        if hook_type not in cls._hooks_map:
            cls._hooks_map[hook_type] = []

        cls._hooks_map[hook_type].append(hook_func)

    @classmethod
    def run_hooks(cls, hook_type, *args, **kwargs):
        hook_funcs = cls._hooks_map.get(hook_type) or []
        for hook_func in hook_funcs:
            hook_func(*args, **kwargs)


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""

    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass

    return False


def get_function_name(func):
    if six.PY2:
        if hasattr(func, "im_class"):
            return "%s.%s" % (func.im_class, func.__name__)
        else:
            return "%s.%s" % (func.__module__, func.__name__)
    else:
        return "%s.%s" % (func.__module__, func.__qualname__)


def _encode(src):
    """remove extra 'u' in PY2."""
    if six.PY2 and isinstance(src, unicode):
        return src.encode('utf-8')
    return src


def unicode_key_value_to_string(src):
    """Recursively converts dictionary keys to strings."""
    if isinstance(src, dict):
        return dict((_encode(k),
                    _encode(unicode_key_value_to_string(v)))
                    for k, v in src.items())
    if isinstance(src, list):
        return [unicode_key_value_to_string(l) for l in src]
    return _encode(src)
