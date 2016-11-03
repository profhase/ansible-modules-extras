#!/usr/bin/python

"""
Ansible module to register SLES hosts
(c) 2016, Ilya Rumyantsev <contact@rumyantsev.de>
Certain parts are taken from Mark Theunissen's mysqldb module
This file is part of Ansible
Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

from ansible.module_utils.basic import AnsibleModule
import json


DOCUMENTATION = """
---
module: suse_register
short_description: Registers a sles / SUSE host at SCC
description:
    - Launches C(SUSEConnect) to register a host at SuSE Customer Center
version_added: '2.3'
author: "Ilya Rumyantsev (@profhase)"
options:
  exec_path:
    description:
      - C(/path/to/SUSEConnect)
    default: /usr/sbin/SUSEConnect

  regcode:
    description:
      - Registration code from the SCC account
      - Required if I(state) = C('registered')

  state:
    description:
      - Registration state of the host
    default: 'registered'
    choices: [ 'registered', 'unregistered' ]

requirements:
  - SLES

"""

EXAMPLES = """
- suse_register: regcode=AAABBD1234

- suse_register: state=unregistered
"""

RETURN = """
  identifier:
    description: Product identifier
    returned: state=='registered'
    type: string
    sample: SLES

  version:
    description: Product version
    returned: state=='registered'
    type: string
    sample: 12.1

  arch:
    description: Product architecture
    returned: state=='registered'
    type: string
    sample: x86_64

  status:
    description: Registration status
    type: string
    sample: "Registered"

  regcode:
    description: Product registration code
    returned: state=='registered'
    type: string
    sample: ABCD1234

  starts_at:
    description: Subscription start
    returned: state=='registered'
    type: date
    sample: 2016-01-01 00:00:00 UTC

  expires_at:
    description: Subscription expiration
    returned: state=='registered'
    type: date
    sample: 2017-01-01 00:00:00 UTC

  subscription_status:
    description: Subscription status (active / not active)
    returned: state=='registered'
    type: str
    sample: ACTIVE

  type:
    description: Subscription type
    returned: state=='registered'
    type: str
    sample: full


"""

STATE_STRINGS = {"Registered": "registered",
                 "Not Registered": "unregistered"}


def change_state(module):
    COMMANDS = {"registered": ["-r", module.params["regcode"]],
                "unregistered": ["-d"]}

    rc, out, err= module.run_command([module.params['exec_path']] +
                             COMMANDS[module.params['state']])

    if rc != 0:
        module.fail_json(changed=False,
                         msg=out)


def check_state(module):
    _, connect_result, err = module.run_command([module.params["exec_path"], "-s"])
    if "Root privileges are required" in err:
        module.fail_json(changed=False,
                         msg="Root rights required, use 'become: True'")
    return json.loads(connect_result)[0]


def main():
    arg_spec = {
        "state": {"default": "registered",
                  "choices": ["registered", "unregistered"]},
        "regcode": {"required": False, "type": "str"},
        "exec_path": {"default": "/usr/sbin/SUSEConnect"}
    }
    module = AnsibleModule(
        argument_spec=arg_spec,
        required_if=[("state", "registered", ["regcode",]),],
        supports_check_mode=True
    )
    facts = check_state(module)

    if STATE_STRINGS[facts['status']] == module.params['state']:
        module.exit_json(changed=False,
                         ansible_facts={"sles_reg_status": facts})
    else:
        if not module.check_mode:
            change_state(module)
            facts = check_state(module)
        module.exit_json(changed=True,
                         ansible_facts={"sles_reg_status": facts})

if __name__ == '__main__':
    main()