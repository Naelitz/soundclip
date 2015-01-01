# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os

from SoundClip.cue import CueStack, Cue
from SoundClip.project import Project
from SoundClip.util import sha


def write_object(root, d):
    """
    Writes an object to the database, returning its sha1 checksum. Like git, objects are keyed by the sha1 hash of their
    content. The first two bytes of the hash refer to the sub directory of the objects store, the remaining 40 bytes
    are the name of the file.

    :param root: The project root directory
    :param d: The dictionary to serialize
    :return: the sha1 checksum that refers to this project
    """
    s = json.dumps(d)
    key = sha(s)

    os.makedirs(os.path.join(root, key[0:2]))

    with open(os.path.join(root, key[0:2], key[3:40]), "w") as f:
        json.dump(d, f)

    return key


def serialize_cue(c: Cue):
    return ""


def serialize_stack(s: CueStack):
    return ""


def serialize_project(p: Project):
    d = p.as_dict()
    d['stacks'] = []

    for stack in p.cue_stacks():
        stack_hash = serialize_stack(stack)
        d['stacks'] += stack_hash

        with open(os.path.join(p.root, 'project.json'), 'w') as f:
            json.dump(d, f)
