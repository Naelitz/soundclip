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

from gi.repository import GObject

from SoundClip.cue import CueStack


class Project(GObject.GObject):
    name = GObject.Property(type=str)
    creator = GObject.Property(type=str)
    root = GObject.property(type=str)
    current_hash = GObject.property(type=str)
    last_hash = GObject.property(type=str)

    def __init__(self, name="Untitled Project", creator="", root="", cue_stacks=None, current_hash=None,
                 last_hash=None):
        GObject.GObject.__init__(self)
        self.name = name
        self.creator = creator
        self.root = root
        self.cue_stacks = [CueStack(), ] if cue_stacks is None else cue_stacks
        self.current_hash = current_hash
        self.last_hash = last_hash

    def close(self):
        # TODO: Stop all playing cues
        # TODO: Save project to disk if new
        # TODO: Commit and close DB connection
        pass

    @staticmethod
    def load(path):
        if not os.path.isdir(os.path.join(path, ".soundclip")):
            raise FileNotFoundError("Path does not exist or not a soundclip project")

        with open(os.path.join(path, ".soundclip", "project.json"), "rt") as dbobj:
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
                stacks += CueStack.load(path, key)

        return Project(name=name, creator=creator, root=path, cue_stacks=stacks, current_hash=sha(content),
                       last_hash=last_hash)

    def store(self):
        d = {'name': self.name, 'creator': self.creator, 'stacks': []}

        for stack in self.cue_stacks:
            stack_hash = stack.store(stack)
            d['stacks'] += stack_hash

            with open(os.path.join(self.root, 'project.json'), 'w') as f:
                json.dump(d, f)