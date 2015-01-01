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
from SoundClip.storage.parser import parse_project


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
    def from_disk(path):
        return parse_project(path)

    def as_dict(self):
        return {'name': self.name, 'creator': self.creator}