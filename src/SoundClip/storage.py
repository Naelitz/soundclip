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

"""
Sound Clip on disk project format

Inspired by git, cues and cue stacks are stored as abstract objects with their hash as their name on disk
Example disk format:

.soundclip/
├── objects
│   ├── 7b
│   │   └── 3fb93c9f3ccbeeb5e6495f9cae38a0c103dcac
│   └── de
│       └── 10623d88eb2f3c4e9e02301901f329ff9bb56c
└── project.json

Cues are serialized to json by the serializer for their specific type. All cues and cuelists contain a pointer to their
previous revisions
"""

import json
import os

from SoundClip.util import sha


def read(root, checksum):
    """
    Reads an object from the database, returning its json content. Like git, objects are keyed by the sha1 hash of their
    content. The first two bytes of the hash refer to the sub directory of the objects store, the remaining 40 bytes
    are the name of the file.

    :param root: The project root directory
    :param checksum: The checksum of the object to read
    :return: the json content of the specified object
    """

    key = sha(checksum)
    path = os.path.join(root, '.soundclip', 'objects', key[0:2], key[2:40])
    if not os.path.exists(path):
        raise FileNotFoundError("The specified object doesn't exist in the database!")

    with open(path, "rt") as dbobj:
        content = dbobj.read()

    if not content:
        # TODO: Illegal Object Exception: empty object!
        return

    assert (sha(content) is checksum)

    return json.loads(content)


def write(root, d, current_hash):
    """
    Writes an object to the database, returning its sha1 checksum. Like git, objects are keyed by the sha1 hash of their
    content. The first two bytes of the hash refer to the sub directory of the objects store, the remaining 40 bytes
    are the name of the file.

    :param root: The project root directory
    :param d: The dictionary to serialize
    :return: the sha1 checksum that refers to this project
    """

    # TODO: Do we need to sort the dictionary so objects with no change always have the same hash?

    s = json.dumps(sorted(d))
    checksum = sha(s)

    # No need to write duplicate objects
    if checksum is current_hash and os.path.exists(os.path.join(root, '.soundclip', 'objects', checksum)):
        return checksum, d['previousRevision']

    d['previousRevision'] = current_hash

    path = os.path.join(root, '.soundclip', 'objects', checksum[0:2])
    os.makedirs(path)
    object_path = os.path.join(path, checksum[2:40])
    print("Writing", object_path)
    with open(object_path, "w") as f:
        json.dump(d, f)

    return checksum, current_hash