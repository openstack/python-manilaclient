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
import six

from oslo_utils import strutils

from manilaclient.common import constants
from manilaclient import exceptions


def extract_key_value_options(pairs):
    result_dict = {}
    duplicate_options = []
    pairs = pairs or {}

    for attr, value in pairs.items():
        if attr not in result_dict:
            result_dict[attr] = value
        else:
            duplicate_options.append(attr)

    if pairs and len(duplicate_options) > 0:
        duplicate_str = ', '.join(duplicate_options)
        msg = "Following options were duplicated: %s" % duplicate_str
        raise exceptions.CommandError(msg)

    return result_dict


def format_properties(properties):
    formatted_data = []

    for item in properties:
        formatted_data.append("%s : %s" % (item, properties[item]))
    return "\n".join(formatted_data)


def extract_properties(properties):
    result_dict = {}
    for item in properties:
        try:
            (key, value) = item.split('=', 1)
            if key in result_dict:
                raise exceptions.CommandError(
                    "Argument '%s' is specified twice." % key)
            else:
                result_dict[key] = value
        except ValueError:
            raise exceptions.CommandError(
                "Parsing error, expected format 'key=value' for " + item
            )
    return result_dict


def extract_extra_specs(extra_specs, specs_to_add):
    for item in specs_to_add:
        (key, value) = item.split('=', 1)
        if key in extra_specs:
            msg = ("Argument '%s' value specified twice." % key)
            raise exceptions.CommandError(msg)
        elif key in constants.BOOL_SPECS:
            if strutils.is_valid_boolstr(value):
                extra_specs[key] = value.capitalize()
            else:
                msg = ("Argument '%s' is of boolean "
                       "type and has invalid value: %s"
                       % (key, six.text_type(value)))
                raise exceptions.CommandError(msg)
        else:
            extra_specs[key] = value
    return extra_specs
