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
    path = os.path.join(root, key[0:2], key[3:40])
    if not os.path.exists(path):
        raise FileNotFoundError("The specified object doesn't exist in the database!")

    with open(path, "rt") as dbobj:
        content = dbobj.read()

    if not content:
        # TODO: Illegal Object Exception: empty object!
        return

    assert (sha(content) is checksum)

    return json.loads(content)


def write(root, d):
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