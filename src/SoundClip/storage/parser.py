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

.soundclip                                            - The Project Object Database
├── objects                                           - All cues, cue stacks, and project metadata ever created for
│   ├── 60                                              this project, ever
│   │   └── fde9c2310b0d4cad4dab8d126b04387efba289
│   └── c8
│       └── f8a1d5ee4b610421aa985274369b26082dfc98
└── project.json                                      - Metadata information for the project, contains a list of cue
                                                        stacks, in the order they occur

Cues are serialized to json by the serializer for their specific type. All cues and cuelists contain a pointer to their
previous revisions

"""

import json
import os
from SoundClip.cue import CueStack, Cue, AutoFollowType
from SoundClip.project import Project

from SoundClip.util import sha


def read_object(root, checksum):
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


def parse_audio_cue(root, cue, j):
    cue.audio_source_uri = j['src'] if 'src' in j else ""

    if not os.path.exists(os.path.join(root, cue.audio_soruce_uri)):
        # TODO: Warn about nonexistent audio file source
        pass

    cue.pitch = float(j['pitch']) if 'pitch' in j else 0.0
    cue.pan = float(j['pan']) if 'pan' in j else 0.0
    cue.gain = float(j['gain']) if 'gain' in j else 0.0
    cue.fade_in_time = int(j['fadeInTime']) if 'fadeInTime' in j else 0
    cue.fade_out_time = int(j['fadeOutTime']) if 'fadeOutTime' in j else 0

    return cue


def parse_cue(root, key):
    j = read_object(root, key)
    if 'type' not in j:
        # TODO: Malformed Cue Exception: Cue does nto specify type error
        return

    c = Cue()

    c.name = j['name'] if 'name' in j else "Untitled Cue"
    c.description = j['description'] if 'description' in j else ""
    c.notes = j['notes'] if 'notes' in j else ""
    c.number = float(j['number']) if 'number' in j else -1.0
    c.pre_wait = int(j['preWait']) if 'preWait' in j else 0
    c.post_wait = int(j['postWait']) if 'postWait' in j else 0

    # TODO: Best way to link a checksum to the proper instance of the cue object
    c.autofollow_target = j['autoFollowTarget'] if 'autoFollowTarget' in j else ""

    c.autofollow_type = AutoFollowType.Trigger if 'autoFollowType' in j and j['autoFollowType'] is 1 else \
        AutoFollowType.StandBy

    c.current_hash = key
    c.last_hash = j['previousRevision'] if 'previousRevision' in j else None

    # TODO: Support custom cue types (plugins)
    t = j['type']
    if t is 'audio':
        return parse_audio_cue(root, c, j)

    # TODO: Unknown Cue Type. Missing plugin?
    return


def parse_cue_stack(root, key):
    j = read_object(root, key)

    name = j['name'] if 'name' in j else "Untitled Cue Stack"
    current_hash = key
    last_hash = j['previousRevision'] if 'previousRevision' in j else None
    cues = []
    if 'cues' in j:
        for cue in j['cues']:
            cues += parse_cue(root, cue)

    return CueStack(name=name, cues=cues, current_hash=current_hash, last_hash=last_hash)


def parse_project(root):
    if not os.path.isdir(os.path.join(root, ".soundclip")):
        raise FileNotFoundError("Path does not exist or not a soundclip project")

    with open(os.path.join(root, ".soundclip", "project.json"), "rt") as dbobj:
        content = dbobj.read()

    if not content:
        # TODO: Corrupted Project: project.json is empty
        return

    j = json.loads(content)

    name = j['name'] if 'name' in j else "Untitled Project"
    creator = j['creator'] if 'creator' in j else ""
    last_hash = j['previousRevision'] if 'previousRevision' in j else None

    stacks = []
    if 'stacks' in j:
        for key in j['stacks']:
            stacks += parse_cue_stack(root, key)

    return Project(name=name, creator=creator, root=root, cue_stacks=stacks, current_hash=sha(content),
                   last_hash=last_hash)


