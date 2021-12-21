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

import logging

from oslo_utils import strutils

from manilaclient.common._i18n import _
from manilaclient.common import constants
from manilaclient import exceptions

LOG = logging.getLogger(__name__)


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


def extract_extra_specs(extra_specs, specs_to_add,
                        bool_specs=constants.BOOL_SPECS):
    try:
        for item in specs_to_add:
            (key, value) = item.split('=', 1)
            if key in extra_specs:
                msg = ("Argument '%s' value specified twice." % key)
                raise exceptions.CommandError(msg)
            elif key in bool_specs:
                if strutils.is_valid_boolstr(value):
                    extra_specs[key] = value.capitalize()
                else:
                    msg = (
                        "Argument '%s' is of boolean "
                        "type and has invalid value: %s"
                        % (key, str(value)))
                    raise exceptions.CommandError(msg)
            else:
                extra_specs[key] = value
    except ValueError:
        msg = LOG.error(_(
            "Wrong format: specs should be key=value pairs."))
        raise exceptions.CommandError(msg)
    return extra_specs


def extract_group_specs(extra_specs, specs_to_add):
    return extract_extra_specs(extra_specs,
                               specs_to_add, constants.GROUP_BOOL_SPECS)


def format_column_headers(columns):
    column_headers = []
    for column in columns:
        column_headers.append(
            column.replace('_', ' ').title().replace('Id', 'ID'))
    return column_headers


def format_share_group_type(share_group_type, formatter='table'):
    printable_share_group_type = share_group_type._info

    is_public = printable_share_group_type.pop('is_public')

    printable_share_group_type['visibility'] = (
        'public' if is_public else 'private')

    if formatter == 'table':
        printable_share_group_type['group_specs'] = (
            format_properties(share_group_type.group_specs))
        printable_share_group_type['share_types'] = (
            "\n".join(printable_share_group_type['share_types'])
        )

    return printable_share_group_type
