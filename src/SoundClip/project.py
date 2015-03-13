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
from logging.handlers import RotatingFileHandler
import os
import logging
logger = logging.getLogger('SoundClip')

from enum import Enum
from gi.repository import GObject

from SoundClip.cue import CueStack
from SoundClip.exception import SCException
from SoundClip.util import sha


class ProjectParserException(SCException):
    pass


class IllegalProjectStateException(SCException):
    pass


class StackChangeAction(Enum):
    INSERT = 0
    UPDATE = 1
    DELETE = 2


class Project(GObject.GObject):

    __gsignals__ = {
        'stack-changed': (GObject.SIGNAL_RUN_FIRST, None, (int, GObject.TYPE_PYOBJECT))
    }

    __MAX_LOG_COUNT__ = 5

    name = GObject.Property(type=str)
    creator = GObject.Property(type=str)
    panic_fade_time = GObject.property(type=GObject.TYPE_LONG)
    panic_hard_stop_time = GObject.property(type=GObject.TYPE_LONG)
    current_hash = GObject.property(type=str)
    last_hash = GObject.property(type=str)

    def __init__(self, name="Untitled Project", creator="", root="", panic_fade_time=500, panic_hard_stop_time=1000,
                 cue_stacks=None, current_hash=None, last_hash=None):
        GObject.GObject.__init__(self)
        self.name = name
        self.creator = creator
        self.__root = root
        self.cue_stacks = [CueStack(project=self), ] if cue_stacks is None else cue_stacks
        self.panic_fade_time = panic_fade_time
        self.panic_hard_stop_time = panic_hard_stop_time
        self.current_hash = current_hash
        self.last_hash = last_hash
        self.__dirty = True

        self.__logfile_handler = None

        self.init_logfile()

    def __iadd__(self, other):
        if not isinstance(other, CueStack):
            raise TypeError("Can't add type {0} to Project".format(type(other)))
        self.cue_stacks.append(other)
        self.emit('stack-changed', len(self.cue_stacks)-1, StackChangeAction.INSERT)

        return self

    def __isub__(self, other):
        if not isinstance(other, CueStack):
            raise TypeError("Can't remove type {0} from Project".format(type(other)))
        elif other not in self.cue_stacks:
            raise ValueError("{0} isn't in this project".format(other))

        key = self.cue_stacks.index(other)
        self.cue_stacks.remove(key)

        self.emit('stack-changed', key, StackChangeAction.DELETE)

        return self

    def __setitem__(self, key, value):
        if not isinstance(value, CueStack):
            raise TypeError("Cannot add type {0} to CueList".format(type(value)))

        i = len(self.cue_stacks)
        self.cue_stacks[key] = value

        self.emit('stack-changed', key, StackChangeAction.UPDATE if 0 <= key < i else StackChangeAction.INSERT)

    def __getitem__(self, key):
        logger.debug("Asked for cuelist in slot {0}".format(key))
        return self.cue_stacks[key]

    def __len__(self):
        return len(self.cue_stacks)

    @GObject.property(type=str)
    def root(self):
        return self.__root

    def change_root(self, path):
        logger.debug("Current Root: {0}".format(self.__root))
        if self.__root and self.__root != path:
            # TODO: Copy project if root is already set
            logger.warning("Need to copy project to new location!")
        else:
            logger.debug("Setting new root {0}".format(path))
            self.__root = path

    def init_logfile(self):
        if self.__root is not None and self.__logfile_handler is None:
            logpath = os.path.join(self.__root, os.path.join(".soundclip", "logs"))

            if not os.path.exists(logpath):
                os.makedirs(logpath)

            self.__logfile_handler = RotatingFileHandler(
                os.path.join(logpath, "soundclip.log"), backupCount=Project.__MAX_LOG_COUNT__
            )
            self.__logfile_handler.setLevel(10)
            self.__logfile_handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s - [%(module)s | %(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d %I:%M:%S %p'
            ))
            logger.addHandler(self.__logfile_handler)
            self.__logfile_handler.doRollover()

            logger.info("Logging to file: {0}".format(os.path.join(logpath, "soundclip.log")))

    def close_logfile(self):
        if self.__logfile_handler is not None:
            logger.removeHandler(self.__logfile_handler)
            self.__logfile_handler = None

    def add_cuelist(self, other):
        if not isinstance(other, CueStack):
            raise TypeError("Can't add type {0} to Project".format(type(other)))
        self.cue_stacks.append(other)
        self.emit('stack-changed', len(self.cue_stacks)-1, StackChangeAction.INSERT)

    def remove_cuelist(self, other):
        if not isinstance(other, CueStack):
            raise TypeError("Can't remove type {0} from Project".format(type(other)))
        elif other not in self.cue_stacks:
            raise ValueError("{0} isn't in this project".format(other))

        key = self.cue_stacks.index(other)
        self.cue_stacks.remove(key)

        self.emit('stack-changed', key, StackChangeAction.DELETE)

    def remove_cue(self, cue):
        for stack in self.cue_stacks:
            if cue in stack:
                stack.remove_cue(cue)

    def get_cue_list_for(self, cue):
        for stack in self.cue_stacks:
            if cue in stack:
                return stack
        return None

    def close(self):
        for stack in self.cue_stacks:
            stack.stop_all()

        self.close_logfile()

        # TODO: Save project to disk if new
        pass

    @staticmethod
    def load(path):
        if not os.path.isdir(os.path.join(path, ".soundclip")):
            raise FileNotFoundError("Path does not exist or not a soundclip project")

        with open(os.path.join(path, ".soundclip", "project.json"), "rt") as dbobj:
            content = dbobj.read()

        if not content:
            raise ProjectParserException({
                "message": "The project is corrupted (project.json was empty)!",
                "path": path
            })

        j = json.loads(content)

        name = j['name'] if 'name' in j else "Untitled Project"
        creator = j['creator'] if 'creator' in j else ""
        panic_fade_time = j['panicFadeTime'] if 'panicFadeTime' in j else 500
        panic_hard_stop_time = j['panicHardStopTime'] if 'panicHardStopTime' in j else 1000
        last_hash = j['previousRevision'] if 'previousRevision' in j else None

        p = Project(name=name, creator=creator, root=path, cue_stacks=[], panic_fade_time=panic_fade_time,
                    panic_hard_stop_time=panic_hard_stop_time, current_hash=sha(content), last_hash=last_hash)

        if 'stacks' in j:
            for key in j['stacks']:
                p += CueStack.load(path, key, p)

        return p

    def store(self):
        if not self.__root:
            raise IllegalProjectStateException({
                "message": "Projects must have a root before they can be saved"
            })

        if not os.path.exists(self.__root) or not os.path.isdir(self.__root):
            os.makedirs(self.__root)

        d = {'name': self.name, 'creator': self.creator, 'stacks': [], 'panicFadeTime': self.panic_fade_time,
             'panicHardStopTime': self.panic_hard_stop_time}

        for stack in self.cue_stacks:
            d['stacks'].append(stack.store(self.__root))

        with open(os.path.join(self.__root, '.soundclip', 'project.json'), 'w') as f:
            json.dump(d, f)
            f.write("\n")

        logger.info("Project {0} saved to {1}".format(self.name, self.__root))