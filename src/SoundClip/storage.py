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
│   ├── 26
│   │   └── 79b924e4d0323d587b853d054c69b650b21430
│   ├── 29
│   │   └── 4dde0494c57b0ea544c5d3d128ad61f0e21862
│   ├── 5f
│   │   └── 9cc9f575bdc32c06614890e0b500c20ab726ea
│   └── a3
│       └── 7d877b431d098389042e10457756da151ae565
└── project.json

Cues are serialized to json by the serializer for their specific type. All cues and cuelists contain a pointer to their
previous revisions
"""

import json
import os
import logging
logger = logging.getLogger('SoundClip')

from SoundClip.exception import SCException
from SoundClip.util import sha


class StorageException(SCException):
    pass


class ChecksumMismatchException(StorageException):
    pass


class IllegalObjectException(StorageException):
    pass


__CACHE = {}


def read(root, key, force_reload=False):
    """
    Reads an object from the database, returning its json content. Like git, objects are keyed by the sha1 hash of their
    content. The first two bytes of the hash refer to the sub directory of the objects store, the remaining 40 bytes
    are the name of the file.

    :param root: The project root directory
    :param key: The checksum of the object to read
    :return: the json content of the specified object
    """
    if key in __CACHE and not force_reload:
        logger.debug("Loading {0} from object cache".format(key))
        return __CACHE[key]
    else:
        logger.debug("Cache-Miss: {0} not yet in object cache".format(key))

    path = os.path.join(root, '.soundclip', 'objects', key[0:2], key[2:40])
    logger.debug("Asked to load {0}, looking for {1}".format(key, path))
    if not os.path.exists(path):
        raise FileNotFoundError("The specified object doesn't exist in the database!")

    with open(path, "rt") as dbobj:
        content = dbobj.read().strip()

    if not content:
        raise IllegalObjectException({
            "message": "The object read from the database returned no content. There was probably an error storing it.",
            "key": key
        })

    checksum = sha(content)
    if checksum != key:
        raise ChecksumMismatchException({
            "message": "Cryptographic Checksum Mismatch. Was expecting {0}, got {1}".format(key, checksum),
            "key": key,
            "checksum": checksum
        })

    obj = json.loads(content)
    __CACHE[key] = obj
    return obj


def write(root, d, current_hash):
    """
    Writes an object to the database, returning its sha1 checksum. Like git, objects are keyed by the sha1 hash of their
    content. The first two bytes of the hash refer to the sub directory of the objects store, the remaining 40 bytes
    are the name of the file.

    :param root: The project root directory
    :param d: The dictionary to serialize
    :return: the sha1 checksum that refers to this project
    """

    if 'previousRevision' not in d:
        d['previousRevision'] = ''

    s = json.dumps(d, sort_keys=True).strip()
    checksum = sha(s)

    logger.debug("Asked to store {0} (current has was {1}, checksum: {2})".format(s, current_hash, checksum))

    path = os.path.join(root, '.soundclip', 'objects', checksum[0:2])

    if not os.path.exists(path):
        os.makedirs(path)

    object_path = os.path.join(path, checksum[2:40])

    # No need to write duplicate objects
    if checksum == current_hash and os.path.exists(object_path):
        logger.debug("{0} is already in the object store, skipping".format(checksum))
        return checksum, d['previousRevision']

    d['previousRevision'] = current_hash

    logger.debug("Writing {0}".format(object_path))
    with open(object_path, "w") as f:
        f.write(s)
        f.write('\n')

    return checksum, current_hash