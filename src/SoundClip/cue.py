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
import os

from enum import Enum
from gi.repository import GObject

from SoundClip import storage
from SoundClip.storage import read, write


class PlaybackActionType(Enum):
    PLAY = 0
    PAUSE = 1
    STOP = 2
    FADE_IN = 3
    FADE_OUT = 4


class PlaybackState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class Cue(GObject.GObject):
    """
    The base cue object

    TODO: Abstract class? Clamping? Automation.
    """

    name = GObject.Property(type=str)
    description = GObject.Property(type=str)
    notes = GObject.Property(type=str)
    number = GObject.Property(type=float)
    pre_wait = GObject.Property(type=GObject.TYPE_LONG)
    post_wait = GObject.Property(type=GObject.TYPE_LONG)
    current_hash = GObject.Property(type=str)
    last_hash = GObject.Property(type=str)

    def __init__(self, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0):
        GObject.GObject.__init__(self)
        self.name = name
        self.description = description
        self.notes = notes
        self.number = number
        self.pre_wait = pre_wait
        self.post_wait = post_wait

    def __len__(self):
        return self.duration()

    def go(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    @GObject.property
    def duration(self):
        return 1000

    @GObject.property
    def elapsed_prewait(self):
        return 0

    @GObject.property
    def elapsed(self):
        return 0

    @GObject.property
    def elapsed_postwait(self):
        return 0

    @GObject.property
    def state(self):
        return PlaybackState.STOPPED

    def load(self, root, key, j):
        """
        Completes the loading of this cue from the specified json dictionary. Make sure you chain up to this super
        method to set the common properties

        :param root: The project's root folder
        :param key: The hash this object was loaded from
        :param j: The json dictionary parsed from the object store
        """
        self.name = j['name'] if 'name' in j else "Untitled Cue"
        self.description = j['description'] if 'description' in j else ""
        self.notes = j['notes'] if 'notes' in j else ""
        self.number = float(j['number']) if 'number' in j else -1.0
        self.pre_wait = int(j['preWait']) if 'preWait' in j else 0
        self.post_wait = int(j['postWait']) if 'postWait' in j else 0

        self.current_hash = key
        self.last_hash = j['previousRevision'] if 'previousRevision' in j else None

    def store(self, root, d):
        """
        Stores the cue in the object repository. If you are creating a custom sub class, make sure you chain up to this
        super method as the last call in your cue's `store` method. This writes the common properties and saves the cue
        to the object store

        :param root: The project root path
        :param d: A dictionary of properties to serialize. Use this when chaining up to super methods
        :return: the hash that this cue was written to the repository to. If the has returned matches the `current_hash`
                    of this cue before storing it, the cue has not changed and no write has taken place for this object
        """
        d['name'] = self.name
        d['description'] = self.description
        d['notes'] = self.notes
        d['number'] = self.number
        d['preWait'] = self.pre_wait
        d['postWait'] = self.post_wait
        d['previousRevision'] = self.last_hash

        self.current_hash, self.last_hash = write(root, d, self.current_hash)

        return self.current_hash

    def get_editor(self):
        """
        Should return a GTK.Widget containing the widgets to create or edit this cue. The widget is returned when the
        editor is closed to `on_editor_closed`. You are responsible for maping the widgets back to the properties of
        custom cues.

        Properties handled by the `Cue` base class do not need to be accounted for, they are handled by SoundClip
        directly
        """
        pass

    def on_editor_closed(self, w):
        """
        Called when the cue editor is closed, and returns the widget passed in `get_editor`. If you are implementing
        a custom cue, you should pull the property values from the widget here and apply them to the cue.

        Properties handled by the `Cue` base class do not need to be accounted for, they are handled by SoundClip
        directly
        """
        pass
GObject.type_register(Cue)


class AudioCue(Cue):
    """
    A basic audio cue

    TODO: clamping
    """

    audio_source_uri = GObject.Property(type=str)
    pitch = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    pan = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    gain = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    fade_in_time = GObject.Property(type=GObject.TYPE_LONG, default=0)
    fade_out_time = GObject.Property(type=GObject.TYPE_LONG, default=0)

    def __init__(self, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0,
                 audio_source_uri="", pitch=0, pan=0, gain=0, fade_in_time=0, fade_out_time=0):
        super().__init__(name, description, notes, number, pre_wait, post_wait)
        self.audio_source_uri = audio_source_uri
        self.pitch = pitch
        self.pan = pan
        self.gain = gain
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time

    def load(self, root, key, j):
        super().load(root, key, j)

        self.audio_source_uri = j['src'] if 'src' in j else ""

        if not os.path.exists(os.path.join(root, self.audio_soruce_uri)):
            # TODO: Warn about nonexistent audio file source
            pass

        self.pitch = float(j['pitch']) if 'pitch' in j else 0.0
        self.pan = float(j['pan']) if 'pan' in j else 0.0
        self.gain = float(j['gain']) if 'gain' in j else 0.0
        self.fade_in_time = int(j['fadeInTime']) if 'fadeInTime' in j else 0
        self.fade_out_time = int(j['fadeOutTime']) if 'fadeOutTime' in j else 0

    def store(self, root, d):
        d['src'] = self.audio_source_uri
        d['pitch'] = self.pitch
        d['pan'] = self.pan
        d['gain'] = self.gain
        d['fadeInTime'] = self.fade_in_time
        d['fadeOutTime'] = self.fade_out_time

        return super().store(root, d)
GObject.type_register(AudioCue)


class ControlCue(Cue):
    pass
GObject.type_register(ControlCue)


def load_cue(root, key):
    """
    Loads the cue identified by the specified hash from the object store and initializes the cue according to its type

    :param root: The project's root folder
    :param key: The hash identifier of the cue to load
    :return: The cue identified by the specified hash
    """
    j = storage.read(root, key)
    if 'type' not in j:
        # TODO: Malformed Cue Exception: Cue does nto specify type error
        return

    t = j['type']
    if t is 'audio':
        return AudioCue().load(root, key, j)
    else:
        # TODO: Unknown Cue Type. Missing plugin?
        return Cue().load(root, key, j)


class CueStack(GObject.GObject):
    name = GObject.property(type=str)
    current_hash = GObject.property(type=str)
    last_hash = GObject.property(type=str)

    def __init__(self, name="Default Cue Stack", cues=None, current_hash=None, last_hash=None):
        GObject.GObject.__init__(self)
        self.name = name
        self.current_hash = current_hash
        self.last_hash = last_hash
        # TODO: Once we're done debugging the layout, remote this default cue, the list should start empty
        self.__cues = [Cue(description="This is a default cue. You should change it!", number=1,
                           pre_wait=500),
                       Cue(name="test", description="Another Cue", number=2,
                           pre_wait=5200),
                       Cue(name="Third!", description="And a third!", number=2,
                           pre_wait=31260)] if cues is None else cues
        pass

    def __len__(self):
        return len(self.__cues)

    def __getitem__(self, key):
        return self.__cues[key]

    def __setitem__(self, key, value):
        self.__cues[key] = value

    def __iter__(self):
        return self.__cues.__iter__()

    def __reversed__(self):
        return CueStack(name=self.name, cues=reversed(self.__cues))

    def __contains__(self, item):
        return item in self.__cues

    def __iadd__(self, other):
        self.__cues.append(other)

    def __isub__(self, other):
        self.__cues.remove(other)

    @staticmethod
    def load(root, key):
        j = read(root, key)

        name = j['name'] if 'name' in j else "Untitled Cue Stack"
        current_hash = key
        last_hash = j['previousRevision'] if 'previousRevision' in j else None
        cues = []
        if 'cues' in j:
            for cue in j['cues']:
                cues.append(load_cue(root, cue))

        return CueStack(name=name, cues=cues, current_hash=current_hash, last_hash=last_hash)

    def store(self, root):
        cues = []

        for cue in self.__cues:
            print("Storing", cue.name)
            cues.append(cue.store(root, {}))

        self.current_hash, self.last_hash = write(root, {'name': self.name, 'cues': cues,
                                                         'previousRevision': self.last_hash}, self.current_hash)
        return self.current_hash

    def stop_all(self):
        for cue in self.__cues:
            cue.stop()