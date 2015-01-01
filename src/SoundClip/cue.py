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

from enum import Enum
from gi.repository import GObject


class AutoFollowType(Enum):
    StandBy = 0
    Trigger = 1


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
    autofollow_target = GObject.Property(type=object)
    autofollow_type = GObject.Property(type=object)
    current_hash = GObject.Property(type=str)
    last_hash = GObject.Property(type=str)

    def __init__(self, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0,
                 autofollow_target=None, autofollow_type=AutoFollowType.StandBy):
        GObject.GObject.__init__(self)
        self.name = name
        self.description = description
        self.notes = notes
        self.number = number
        self.pre_wait = pre_wait
        self.post_wait = post_wait
        self.autofollow_target = autofollow_target
        self.autofollow_type = autofollow_type

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
                 autofollow_target=None, autofollow_type=AutoFollowType.StandBy, audio_source_uri="", pitch=0, pan=0,
                 gain=0, fade_in_time=0, fade_out_time=0):
        super().__init__(name, description, notes, number, pre_wait, post_wait, autofollow_target, autofollow_type)
        self.audio_source_uri = audio_source_uri
        self.pitch = pitch
        self.pan = pan
        self.gain = gain
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
GObject.type_register(AudioCue)


class ControlCue(Cue):
    pass
GObject.type_register(ControlCue)


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
        self.__cues = [Cue(description="This is a default cue. You should change it!", pre_wait=500), ] if cues is None else cues
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