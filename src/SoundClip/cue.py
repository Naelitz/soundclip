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
import logging
from SoundClip.audio import PlaybackController

logger = logging.getLogger('SoundClip')

from enum import Enum
from gi.repository import GObject, Gtk

from SoundClip import storage
from SoundClip.exception import SCException
from SoundClip.storage import read, write


class MalformedCueException(SCException):
    pass


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

    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    name = GObject.Property(type=str)
    description = GObject.Property(type=str)
    notes = GObject.Property(type=str)
    number = GObject.Property(type=float)
    pre_wait = GObject.Property(type=GObject.TYPE_LONG)
    post_wait = GObject.Property(type=GObject.TYPE_LONG)
    current_hash = GObject.Property(type=str)
    last_hash = GObject.Property(type=str)

    def __init__(self, project, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0):
        GObject.GObject.__init__(self)

        self.__project = project

        self.name = name
        self.description = description
        self.notes = notes
        self.number = number
        self.pre_wait = pre_wait
        self.post_wait = post_wait

    def __len__(self):
        return self.duration

    def go(self):
        logger.debug("(CUE) GO received for [{0:g}]{1}".format(self.number, self.name))

    def pause(self):
        logger.debug("PAUSE received for [{0:g}]{1}".format(self.number, self.name))

    def stop(self, fade=0):
        logger.debug("STOP received for [{0:g}]{1}".format(self.number, self.name))

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

        return self

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

    def on_editor_closed(self, w, save=True):
        """
        Called when the cue editor is being closed, and returns the widget passed in `get_editor`. If you are
        implementing a custom cue, you should pull the property values from the widget here and apply them to the cue.

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

    pitch = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    pan = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    gain = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    fade_in_time = GObject.Property(type=GObject.TYPE_LONG, default=0)
    fade_out_time = GObject.Property(type=GObject.TYPE_LONG, default=0)

    def __init__(self, project, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0,
                 audio_source_uri="", pitch=0, pan=0, gain=0, fade_in_time=0, fade_out_time=0):
        super().__init__(project, name, description, notes, number, pre_wait, post_wait)

        logger.debug("Init Audio Cue")

        self.__project = project

        self.__src = audio_source_uri
        self.pitch = pitch
        self.pan = pan
        self.gain = gain
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        if os.path.isfile(os.path.abspath(os.path.join(project.root, self.__src))):
            self.__pbc = PlaybackController("file://" + os.path.abspath(os.path.join(project.root, self.__src)))
            self.__pbc.preroll()
            self.__pbc.connect('tick', lambda *x: self.emit('update'))
        else:
            self.__pbc = None

    @property
    def audio_source_uri(self):
        return self.__src

    def change_source(self, src):
        self.__src = src
        logger.debug("Audio source changed for {0} to {1}, changing playback controller".format(self.name, src))
        if self.__pbc is not None and self.__pbc.playing:
            self.__pbc.stop()
        self.__pbc = PlaybackController("file://" + os.path.abspath(os.path.join(self.__project.root, src)))
        self.__pbc.connect('tick', lambda *x: self.emit('update'))
        self.__pbc.preroll()

    @GObject.Property
    def duration(self):
        return self.__pbc.get_duration()

    @GObject.property
    def elapsed(self):
        return self.__pbc.get_position()

    def get_editor(self):
        return SCAudioCueEditorWidget(self, self.__project.root)

    def on_editor_closed(self, w, save=True):
        if save:
            self.change_source(w.get_source())
            self.pitch = w.get_pitch()
            self.pan = w.get_pan()
            self.gain = w.get_gain()
            self.fade_in_time = w.get_fade_in_time()
            self.fade_out_time = w.get_fade_out_time()

    def go(self):
        super().go()
        self.play()
        self.emit('update')

    def play(self, fade=0):
        self.__pbc.play(fade=fade)
        self.emit('update')

        # TODO: Prewait / Postwait timers
        # TODO: Register timer to update progress bars

    def pause(self, fade=0):
        super().pause()
        self.__pbc.pause(fade=fade)
        self.emit('update')

    def stop(self, fade=0):
        super().stop(fade)
        self.__pbc.stop(fade)
        self.emit('update')

    @GObject.property
    def state(self):
        return PlaybackState.PLAYING if self.__pbc.playing else \
            PlaybackState.PAUSED if self.__pbc.paused else PlaybackState.STOPPED

    def load(self, root, key, j):
        super().load(root, key, j)

        self.change_source(j['src'] if 'src' in j else "")

        if not os.path.exists(os.path.join(root, self.audio_source_uri)):
            # TODO: Warn about nonexistent audio file source
            pass

        self.pitch = float(j['pitch']) if 'pitch' in j else 0.0
        self.pan = float(j['pan']) if 'pan' in j else 0.0
        self.gain = float(j['gain']) if 'gain' in j else 0.0
        self.fade_in_time = int(j['fadeInTime']) if 'fadeInTime' in j else 0
        self.fade_out_time = int(j['fadeOutTime']) if 'fadeOutTime' in j else 0

        return self

    def store(self, root, d):
        d['src'] = self.audio_source_uri
        d['pitch'] = self.pitch
        d['pan'] = self.pan
        d['gain'] = self.gain
        d['fadeInTime'] = self.fade_in_time
        d['fadeOutTime'] = self.fade_out_time
        d['type'] = 'audio'

        return super().store(root, d)
GObject.type_register(AudioCue)


class SCAudioCueEditorWidget(Gtk.Grid):
    def __init__(self, cue, root, **properties):
        super().__init__(**properties)

        self.__root = root

        source_label = Gtk.Label("Source:")
        source_label.set_halign(Gtk.Align.END)
        self.attach(source_label, 0, 0, 1, 1)
        self.__source_entry = Gtk.Entry()
        self.__source_entry.set_text(cue.audio_source_uri)
        self.__source_entry.set_hexpand(True)
        self.__source_entry.set_halign(Gtk.Align.FILL)
        self.attach(self.__source_entry, 1, 0, 1, 1)
        source_button = Gtk.Button("...")
        source_button.connect('clicked', self.on_source)
        self.attach(source_button, 2, 0, 1, 1)

        pitch_label = Gtk.Label("Pitch Adjustment:")
        pitch_label.set_halign(Gtk.Align.END)
        self.attach(pitch_label, 0, 1, 1, 1)
        self.__pitch_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.__pitch_scale.set_value(cue.pitch)
        self.__pitch_scale.set_hexpand(True)
        self.__pitch_scale.set_halign(Gtk.Align.FILL)
        self.attach(self.__pitch_scale, 1, 1, 2, 1)

        pan_adjustment = Gtk.Label("Pan Adjustment:")
        pan_adjustment.set_halign(Gtk.Align.END)
        self.attach(pan_adjustment, 0, 2, 1, 1)
        self.__pan_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.__pan_scale.set_value(cue.pan)
        self.__pan_scale.set_hexpand(True)
        self.__pan_scale.set_halign(Gtk.Align.FILL)
        self.attach(self.__pan_scale, 1, 2, 2, 1)

        gain_label = Gtk.Label("Gain Adjustment:")
        gain_label.set_halign(Gtk.Align.END)
        self.attach(gain_label, 0, 3, 1, 1)
        self.__gain_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.__gain_scale.set_value(cue.gain)
        self.__gain_scale.set_hexpand(True)
        self.__gain_scale.set_halign(Gtk.Align.FILL)
        self.attach(self.__gain_scale, 1, 3, 2, 1)

        fade_in_label = Gtk.Label("Fade In Time:")
        fade_in_label.set_halign(Gtk.Align.END)
        self.attach(fade_in_label, 0, 4, 1, 1)
        self.__fade_in_time_entry = Gtk.Entry()
        self.__fade_in_time_entry.set_text(str(cue.fade_in_time))
        self.__fade_in_time_entry.set_hexpand(True)
        self.__fade_in_time_entry.set_halign(Gtk.Align.FILL)
        self.attach(self.__fade_in_time_entry, 1, 4, 2, 1)

        fade_out_label = Gtk.Label("Fade Out Time:")
        fade_out_label.set_halign(Gtk.Align.END)
        self.attach(fade_out_label, 0, 5, 1, 1)
        self.__fade_out_time_entry = Gtk.Entry()
        self.__fade_out_time_entry.set_text(str(cue.fade_out_time))
        self.__fade_out_time_entry.set_hexpand(True)
        self.__fade_out_time_entry.set_halign(Gtk.Align.FILL)
        self.attach(self.__fade_out_time_entry, 1, 5, 2, 1)

    def on_source(self, button):
        dialog = Gtk.FileChooserDialog("Select Audio File",
                                       button.get_parent().get_parent().get_parent().get_parent().get_parent().get_parent(),
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        # TODO: Set initial directory to project root

        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            p = dialog.get_filename()
            r = os.path.relpath(p, start=self.__root)

            # TODO: Validate path

            self.__source_entry.set_text(r)
        elif result == Gtk.ResponseType.CANCEL:
            logger.debug("CANCEL")

        dialog.destroy()

    def get_source(self):
        return self.__source_entry.get_text()

    def get_pitch(self):
        return self.__pitch_scale.get_value()

    def get_pan(self):
        return self.__pan_scale.get_value()

    def get_gain(self):
        return self.__gain_scale.get_value()

    def get_fade_in_time(self):
        return self.__fade_in_time_entry.get_text()

    def get_fade_out_time(self):
        return self.__fade_out_time_entry.get_text()


class ControlCue(Cue):
    pass
GObject.type_register(ControlCue)


def load_cue(root, key, project):
    """
    Loads the cue identified by the specified hash from the object store and initializes the cue according to its type

    :param root: The project's root folder
    :param key: The hash identifier of the cue to load
    :return: The cue identified by the specified hash
    """
    j = storage.read(root, key)
    if 'type' not in j:
        raise MalformedCueException({
            "message": "{0} does not specify a cue type".format(j['name'] if 'name' in j else "The cue being loaded"),
            "key": key,
            "root": root
        })

    t = j['type'] if 'type' in j else 'unknown'
    logger.debug("Trying to load {0} which is of type {1}".format(key, t))
    if t == 'audio':
        return AudioCue(project=project).load(root, key, j)
    else:
        # TODO: Unknown Cue Type. Missing plugin?
        return Cue(project=project).load(root, key, j)


class CueStackChangeType(Enum):
    INSERT = 0
    UPDATE = 1
    DELETE = 2


class CueStack(GObject.GObject):
    __gsignals__ = {
        'changed': (GObject.SIGNAL_RUN_FIRST, None, (int, GObject.TYPE_PYOBJECT)),
        'renamed': (GObject.SIGNAL_RUN_FIRST, None, (str, ))
    }

    name = GObject.property(type=str)
    current_hash = GObject.property(type=str)
    last_hash = GObject.property(type=str)

    def __init__(self, project, name="Default Cue Stack", cues=None, current_hash=None, last_hash=None):
        GObject.GObject.__init__(self)

        self.__project = project

        self.name = name
        self.current_hash = current_hash
        self.last_hash = last_hash

        self.__cues = [] if cues is None else cues

        for cue in self.__cues:
            cue.connect('update', lambda *x: self.emit('changed', self.__cues.index(cue), CueStackChangeType.UPDATE))

    def __len__(self):
        return len(self.__cues)

    def __getitem__(self, key):
        return self.__cues[key]

    def __setitem__(self, key, value):
        if not isinstance(value, Cue):
            raise TypeError("Cannot add type {0} to CueList".format(type(value)))

        l = len(self.__cues)
        self.__cues[key] = value

        self.emit('changed', key, CueStackChangeType.UPDATE if 0 <= key < l else CueStackChangeType.INSERT)
        value.connect('update', lambda *x: self.emit('changed', key, CueStackChangeType.UPDATE))

    def __iter__(self):
        return self.__cues.__iter__()

    def __reversed__(self):
        return CueStack(name=self.name, cues=reversed(self.__cues), project=self.__project)

    def __contains__(self, item):
        return item in self.__cues

    def __iadd__(self, other):
        if not isinstance(other, Cue):
            raise TypeError("Cannot add type {0} to CueList".format(type(other)))

        self.__cues.append(other)
        self.emit('changed', len(self.__cues)-1, CueStackChangeType.INSERT)
        other.connect('update', lambda *x: self.emit('changed', self.__cues.index(other), CueStackChangeType.UPDATE))
        return self

    def __isub__(self, other):
        if not isinstance(other, Cue):
            raise TypeError("Cannot add type {0} to CueList".format(type(other)))

        i = self.__cues.index(other)
        self.__cues.remove(other)
        self.emit('changed', i, CueStackChangeType.DELETE)
        return self

    def index(self, obj):
        return self.__cues.index(obj)

    def add_cue_relative_to(self, existing, cue):
        self.__cues.insert(self.index(existing)+1, cue)
        self.emit('changed', self.index(existing)+1, CueStackChangeType.INSERT)
        cue.connect('changed', self.index(cue), CueStackChangeType.UPDATE)

    @staticmethod
    def load(root, key, project):
        j = read(root, key)

        name = j['name'] if 'name' in j else "Untitled Cue Stack"
        current_hash = key
        last_hash = j['previousRevision'] if 'previousRevision' in j else None
        cues = []
        if 'cues' in j:
            for cue in j['cues']:
                c = load_cue(root, cue, project)
                logger.debug("Loaded {0}".format(repr(c)))
                cues.append(c)

        return CueStack(name=name, cues=cues, current_hash=current_hash, last_hash=last_hash, project=project)

    def store(self, root):
        cues = []

        for cue in self.__cues:
            logger.debug("Storing {0}".format(cue.name))
            cues.append(cue.store(root, {}))

        self.current_hash, self.last_hash = write(root, {'name': self.name, 'cues': cues,
                                                         'previousRevision': self.last_hash}, self.current_hash)
        return self.current_hash

    def rename(self, name):
        self.name = name
        self.emit('renamed', name)
        logger.debug("CueList renamed to {0}".format(name))

    def stop_all(self, fade=0):
        for cue in self.__cues:
            cue.stop(fade=fade)