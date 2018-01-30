# Copyright 2014 SUSE Linux GmbH
#
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

import os
import sys
import cStringIO


def _get_cli_output():
    stdout_org = sys.stdout
    sys.stdout = output = cStringIO.StringIO()
    from manilaclient import shell
    shell = shell.OpenStackManilaShell()
    shell.main(None)
    sys.stdout = stdout_org
    output.seek(0)
    return map(lambda x: "    %s" % x, output)


def builder_inited(app):
    # generate the missing rst files
    with open(os.path.join(app.env.srcdir, "cli/manila_cli_output.rst.inc"), "w") as f:
        f.write("``manila help``::\n\n")
        f.write("\n".join(_get_cli_output()))
        f.write("\n")


def setup(app):
    app.connect('builder-inited', builder_inited)

