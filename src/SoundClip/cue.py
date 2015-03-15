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
import shutil
from SoundClip.audio import PlaybackController
from SoundClip.gui.widgets import TimePicker
from SoundClip.util import Timer

logger = logging.getLogger('SoundClip')

from enum import Enum
from gi.repository import GLib, GObject, Gtk

from SoundClip import storage, util
from SoundClip.exception import SCException
from SoundClip.storage import read, write


class MalformedCueException(SCException):
    pass


class CircularReferenceException(SCException):
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


__PROGRESS_UPDATE_INTERVAL__ = 100


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

        self._project = project

        self.name = name
        self.description = description
        self.notes = notes
        self.number = number
        self.pre_wait = pre_wait
        self.__elapsed_pre_wait = 0
        self.post_wait = post_wait

    def __len__(self):
        return self.duration

    def go(self):
        logger.debug("(CUE) GO received for [{0:g}]{1}".format(self.number, self.name))
        if self.pre_wait <= 0:
            self.action()
        else:
            t = Timer(self.pre_wait, __PROGRESS_UPDATE_INTERVAL__)

            def timeout(opt, progress):
                self.__elapsed_pre_wait = progress
                self.emit('update')

            def expire(opt):
                self.__elapsed_pre_wait = 0
                self.action()

            t.connect('update', timeout)
            t.connect('expired', expire)

            t.fire()

    def action(self):
        logger.debug("(CUE) Starting action for [{0:g}]{1}".format(self.number, self.name))

    def pause(self):
        logger.debug("PAUSE received for [{0:g}]{1}".format(self.number, self.name))

    def stop(self, fade=0):
        logger.debug("STOP received for [{0:g}]{1}".format(self.number, self.name))

    @GObject.property
    def duration(self):
        return 0

    @GObject.property
    def elapsed_prewait(self):
        return self.__elapsed_pre_wait

    @GObject.property
    def elapsed(self):
        return 0

    @GObject.property
    def elapsed_postwait(self):
        return 0

    @GObject.property
    def state(self):
        return PlaybackState.STOPPED

    def validate(self):
        """
        Validate the cue. Cues that are valid should return `None` for this method. Cues with validation errors
        should return a dictionary describing all errors. For example:

        An audio cue file is missing:

        {'Missing Target': "The audio file {0} could not be found."}

        :return:
        """
        return None

    def load(self, root, key, j):
        """
        Completes the loading of this cue from the specified json dictionary. Make sure you chain up to this super
        method to set the common properties

        :param root: The project's root folder
        :param key: The hash this object was loaded from
        :param j: The json dictionary parsed from the object store
        """
        self.name = util.pick(j, 'name', "Untitled Cue")
        self.description = util.pick(j, 'description', "")
        self.notes = util.pick(j, 'notes', "")
        self.number = float(util.pick(j, 'number', -1.0))
        self.pre_wait = int(util.pick(j, 'preWait', 0))
        self.post_wait = int(util.pick(j, 'postWait', 0))

        self.current_hash = key
        self.last_hash = util.pick(j, 'previousRevision', None)

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

    class Editor(Gtk.Grid):
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
            self.__fade_in_time_picker = TimePicker(cue.fade_in_time)
            self.__fade_in_time_picker.set_hexpand(True)
            self.__fade_in_time_picker.set_halign(Gtk.Align.FILL)
            self.attach(self.__fade_in_time_picker, 1, 4, 2, 1)

            fade_out_label = Gtk.Label("Fade Out Time:")
            fade_out_label.set_halign(Gtk.Align.END)
            self.attach(fade_out_label, 0, 5, 1, 1)
            self.__fade_out_time_picker = TimePicker(cue.fade_out_time)
            self.__fade_out_time_picker.set_hexpand(True)
            self.__fade_out_time_picker.set_halign(Gtk.Align.FILL)
            self.attach(self.__fade_out_time_picker, 1, 5, 2, 1)

        def on_source(self, button):
            dialog = Gtk.FileChooserDialog("Select Audio File",
                                           button.get_parent().get_parent().get_parent().get_parent().get_parent().get_parent(),
                                           Gtk.FileChooserAction.OPEN,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK))
            dialog.set_default_size(800, 400)
            dialog.set_current_folder(self.__root)

            result = dialog.run()
            if result == Gtk.ResponseType.OK:
                p = dialog.get_filename()

                if not PlaybackController.is_file_supported(p):
                    logger.warning("Unsupported File '{0}'".format(p))
                    d = Gtk.MessageDialog(dialog, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Unsupported File Type")
                    d.format_secondary_text("'{0}' is not in a format supported by this system.".format(p))
                    d.run()
                    d.destroy()
                    p = ""
                elif not util.in_directory(p, self.__root):
                    logger.warning("The requested file '{0}' is not in the project root".format(p))
                    d = Gtk.MessageDialog(dialog, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL,
                                          "'{0}' is not in the project root!".format(p))
                    d.format_secondary_text("It must be copied to the project root before it can be used")

                    sub_result = d.run()
                    if sub_result == Gtk.ResponseType.OK:
                        logger.info("Copying '{0}' into the project root".format(p))
                        new_path = os.path.join(self.__root, os.path.split(p)[1])
                        shutil.copy2(p, new_path)
                        p = new_path
                        d.destroy()
                    else:
                        d.destroy()
                        dialog.destroy()
                        return

                r = os.path.relpath(p, start=self.__root) if p else ""

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
            return self.__fade_in_time_picker.get_total_milliseconds()

        def get_fade_out_time(self):
            return self.__fade_out_time_picker.get_total_milliseconds()

    pitch = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    pan = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    gain = GObject.Property(type=float, minimum=-1.0, maximum=1.0)
    fade_in_time = GObject.Property(type=GObject.TYPE_LONG, default=0)
    fade_out_time = GObject.Property(type=GObject.TYPE_LONG, default=0)

    def __init__(self, project, name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0,
                 audio_source_uri="", pitch=0, pan=0, gain=0, fade_in_time=0, fade_out_time=0):
        super().__init__(project, name, description, notes, number, pre_wait, post_wait)

        logger.debug("Init Audio Cue")

        self.__src = audio_source_uri
        self.pitch = pitch
        self.pan = pan
        self.gain = gain
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        if os.path.isfile(os.path.abspath(os.path.join(project.root, self.__src))):
            self.__pbc = PlaybackController("file://" + os.path.abspath(os.path.join(project.root, self.__src)))
            self.__pbc.preroll()
        else:
            self.__pbc = None

    @property
    def audio_source_uri(self):
        return self.__src

    def seek(self, ms):
        target = self.elapsed + ms
        if target < 0:
            self.__pbc.seek(0)
        elif target > self.duration:
            self.stop()
        else:
            self.__pbc.seek(target)
        self.emit('update')

    def __update_func(self):
        self.emit('update')
        return self.__pbc.playing

    def change_source(self, src):
        self.__src = src
        logger.debug("Audio source changed for {0} to {1}, changing playback controller".format(self.name, src))
        if self.__pbc is not None and self.__pbc.playing:
            self.__pbc.stop()
        self.__pbc = PlaybackController("file://" + os.path.abspath(os.path.join(self._project.root, src)))
        self.__pbc.preroll()

    @GObject.Property
    def duration(self):
        return self.__pbc.get_duration()

    @GObject.property
    def elapsed(self):
        return self.__pbc.get_position()

    def get_editor(self):
        return AudioCue.Editor(self, self._project.root)

    def on_editor_closed(self, w, save=True):
        if save:
            self.change_source(w.get_source())
            self.pitch = w.get_pitch()
            self.pan = w.get_pan()
            self.gain = w.get_gain()
            self.fade_in_time = w.get_fade_in_time()
            self.fade_out_time = w.get_fade_out_time()

            # We need to preroll the playback controller in order to get the length of the audio file
            self.__pbc.preroll()
            self.__pbc.stop()

    def action(self):
        super().action()

        self.__pbc.play(fade=self.fade_in_time)
        self.emit('update')
        GLib.timeout_add(__PROGRESS_UPDATE_INTERVAL__, self.__update_func)

        # TODO: Schedule Fade Out
        self.emit('update')

    def fade_to(self, target_volume, duration, callback=None):
        self.__pbc.fade_to(target_volume, duration, callback)

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

    def validate(self):
        errors = {}

        if not self.audio_source_uri:
            errors['Missing File'] = "No audio file specified"
        elif not os.path.exists(os.path.join(self._project.root, self.audio_source_uri)) and \
                os.path.isfile(os.path.join(self._project.root, self.audio_source_uri)):
            errors['Missing File'] = "{0} could not be found".format(self.audio_source_uri)
        elif not PlaybackController.is_file_supported(os.path.join(self._project.root, self.audio_source_uri)):
            errors['Unsupported File'] = "{0} is not a supported audio file".format(self.audio_source_uri)

        return errors if errors else None

    def load(self, root, key, j):
        super().load(root, key, j)

        self.change_source(j['src'] if 'src' in j else "")

        if not os.path.exists(os.path.join(root, self.audio_source_uri)):
            logger.warning("Audio file does not exists in project root!")

            # TODO: Register error with project

            pass

        self.pitch = float(util.pick(j, 'pitch', 0.0))
        self.pan = float(util.pick(j, 'pan', 0.0))
        self.gain = float(util.pick(j, 'gain', 0.0))
        self.fade_in_time = int(util.pick(j, 'fadeInTime', 0))
        self.fade_out_time = int(util.pick(j, 'fadeOutTime', 0))

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


class CuePointer(GObject.Object):

    def __init__(self, cue, target=None, index=0):
        super().__init__()

        if target is not None and index is not 0:
            raise ValueError("Cue Pointer target must be either specific or relative, not both")
        elif target is None and index is 0:
            raise ValueError("Cue Pointer must have a target")

        self.__cue = cue
        self.__target = target
        self.__relative_index = index

    @GObject.property(type=bool, default=False)
    def is_relative(self):
        return self.__target is None

    @GObject.property(type=GObject.Object)
    def target(self):
        return self.__target

    @GObject.property(type=GObject.TYPE_LONG)
    def relative_index(self):
        return self.__relative_index

    def resolve(self, project):
        if self.is_relative:
            return project.get_cue_list_for(self.__cue).get_cue_relative_to(self.__cue, self.relative_index)
        else:
            return self.target
GObject.type_register(CuePointer)


class ControlCue(Cue):

    target_volume = GObject.property(type=float, minimum=0.0, maximum=10.0)
    fade_duration = GObject.property(type=GObject.TYPE_LONG)
    stop_target_on_volume_reached = GObject.property(type=bool, default=True)

    class Editor(Gtk.Grid):

        def __init__(self, project, cue, **properties):
            super().__init__(**properties)

            self.__project = project
            self.__cue = cue

            self.attach(Gtk.Label("Target Cue List:"), 0, 0, 1, 1)
            self.__stack_store = Gtk.ListStore(int, str)

            global select
            select = -1
            for i in range(0, len(self.__project)):
                c = self.__project[i]
                self.__stack_store.append([i, c.name])
                if self.__cue.target is not None and c is self.__project.get_cue_list_for(
                        self.__cue.target.resolve(self.__project)):
                    select = i
            self.__stack_combo = Gtk.ComboBox.new_with_model(self.__stack_store)
            if select >= 0:
                logger.debug("Setting initial cue list to {0}".format(select))
                self.__stack_combo.set_active(select)

            stack_name_renderer = Gtk.CellRendererText()
            self.__stack_combo.pack_start(stack_name_renderer, True)
            self.__stack_combo.add_attribute(stack_name_renderer, 'text', 1)
            self.__stack_combo.set_hexpand(True)
            self.__stack_combo.set_halign(Gtk.Align.FILL)
            self.attach(self.__stack_combo, 1, 0, 1, 1)

            self.attach(Gtk.Label("Target Cue: "), 0, 1, 1, 1)
            self.__cue_store = Gtk.ListStore(int, str)
            self.__target_combo = Gtk.ComboBox.new_with_model(self.__cue_store)

            cl = self.__project.get_cue_list_for(
                self.__cue if self.__cue.target is None else self.__cue.target.resolve(self.__project)
            )
            self.__cue_selector_initialized = False if self.__cue.target is not None else True
            self.populate_stack_combo(cl if cl is not None else self.__project[0])

            cue_name_renderer = Gtk.CellRendererText()
            self.__target_combo.pack_start(cue_name_renderer, True)
            self.__target_combo.add_attribute(cue_name_renderer, 'text', 1)
            self.__target_combo.set_hexpand(True)
            self.__target_combo.set_halign(Gtk.Align.FILL)
            self.attach(self.__target_combo, 1, 1, 1, 1)

            self.__stack_combo.set_active(0)
            self.__stack_combo.connect('changed', self.on_list_selected)

            self.attach(Gtk.Label("Target Volume: "), 0, 2, 1, 1)
            self.__target_vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1.0, 0.1)
            self.__target_vol.set_value(self.__cue.target_volume if self.__cue is not None else 0.0)
            self.__target_vol.set_hexpand(True)
            self.__target_vol.set_halign(Gtk.Align.FILL)
            self.attach(self.__target_vol, 1, 2, 1, 1)

            self.attach(Gtk.Label("Fade Duration:"), 0, 3, 1, 1)
            self.__fade_duration = TimePicker(initial_milliseconds=self.__cue.fade_duration if self.__cue else 0)
            self.attach(self.__fade_duration, 1, 3, 1, 1)

            self.__stop_on_target_volume = Gtk.CheckButton("Stop Target Cue on Complete")
            self.__stop_on_target_volume.set_active(self.__cue.stop_target_on_volume_reached)
            self.attach(self.__stop_on_target_volume, 0, 4, 2, 1)

        def on_list_selected(self, combo):
            itr = combo.get_active_iter()
            if itr is not None:
                model = combo.get_model()
                index = model[itr][0]
                if index >= 0:
                    self.populate_stack_combo(self.__project[index])

        def populate_stack_combo(self, stack):
            global select
            select = -1
            self.__cue_store = Gtk.ListStore(int, str)
            for i in range(0, len(stack)):
                self.__cue_store.append([i, stack[i].name])
                if not self.__cue_selector_initialized and stack[i] is self.__cue.target.resolve(self.__project):
                    select = i
                    self.__cue_selector_initialized = True
            self.__target_combo.set_model(self.__cue_store)
            if select >= 0:
                logger.debug("Setting initially selected target index to {0}".format(select))
                self.__target_combo.set_active(select)

        def results(self):
            return {
                'type': 'absolute',
                'target': (self.__project[self.__stack_combo.get_active()])[self.__target_combo.get_active()],
                'targetVolume': self.__target_vol.get_value(),
                'duration': self.__fade_duration.get_total_milliseconds(),
                'stopOnComplete': self.__stop_on_target_volume.get_active()
            }

    def __init__(self, project, target, target_volume, fade_duration, stop_target_on_volume_reached=True,
                 name="Untitled Cue", description="", notes="", number=-1.0, pre_wait=0, post_wait=0):
        super().__init__(project, name=name, description=description, notes=notes, number=number, pre_wait=pre_wait,
                         post_wait=post_wait)

        if target is not None and target is not isinstance(target, CuePointer):
            raise ValueError("{0} is not a cue pointer!".format(str(type(target))))

        self.__target = target
        self.target_volume = target_volume
        self.fade_duration = fade_duration
        self.stop_target_on_volume_reached = stop_target_on_volume_reached

        self.__elapsed = 0
        self.__state = PlaybackState.STOPPED

    @GObject.Property
    def duration(self):
        return self.fade_duration

    @GObject.Property
    def elapsed(self):
        return self.__elapsed

    def get_editor(self):
        return ControlCue.Editor(self._project, self)

    def on_editor_closed(self, w, save=True):
        if save:
            data = w.results()
            if data['type'] is 'absolute':
                self.__target = CuePointer(self, target=data['target'])
            else:
                self.__target = CuePointer(self, index=int(data['target']))
            self.target_volume = float(data['targetVolume'])
            self.fade_duration = int(data['duration'])
            self.stop_target_on_volume_reached = data['stopOnComplete']
            self.emit('update')

    @GObject.Property
    def state(self):
        return self.__state

    def go(self):
        super().go()
        self.__state = PlaybackState.PLAYING

    def action(self):
        super().action()

        if self.target is not None:
            c = self.target.resolve(self._project)
            if self.stop_target_on_volume_reached:
                c.stop(fade=self.fade_duration)
            elif isinstance(c, AudioCue):
                c.fade_to(target_volume=self.target_volume, duration=self.fade_duration)

        t = Timer(self.fade_duration, __PROGRESS_UPDATE_INTERVAL__)

        def timeout(opt, progress):
            self.__elapsed = progress
            self.emit('update')

        def expire(opt):
            self.__elapsed = 0
            self.__state = PlaybackState.STOPPED

        t.connect('update', timeout)
        t.connect('expired', expire)

        t.fire()

    @GObject.property
    def target(self):
        return self.__target

    def validate(self):
        errors = {}

        if self.__target.resolve(self._project) is None:
            errors['No Target'] = "This cue has no target or the target it referenced no longer exists"

        return errors if errors else None

    def load(self, root, key, j):
        super().load(root, key, j)

        self.target_volume = float(util.pick(j, 'targetVolume', 0.0))
        self.fade_duration = int(util.pick(j, 'fadeDuration', 0))
        self.stop_target_on_volume_reached = bool(util.pick(j, 'stopTargetOnVolumeReached', True))
        if j['target']['type'] is 'relative':
            self.__target = CuePointer(cue=self, index=j['target']['index'])
        else:
            self.__target = CuePointer(cue=self, target=load_cue(
                root, j['target']['ref'], self._project
            ) if 'target' in j else None)

        return self

    def store(self, root, d):
        d['targetVolume'] = self.target_volume
        d['fadeDuration'] = self.fade_duration
        d['stopTargetOnVolumeReached'] = self.stop_target_on_volume_reached
        d['target'] = {
            'ref': self.target.resolve(self._project).store(root, {}),
            'type': 'relative' if self.target.is_relative else 'absolute',
            'index': self.target.relative_index if self.target.is_relative else -1
        }
        d['type'] = 'control'

        return super().store(root, d)
GObject.type_register(ControlCue)

__LOAD_STACK = []
__CUE_CACHE = {}


def load_cue(root, key, project):
    """
    Loads the cue identified by the specified hash from the object store and initializes the cue according to its type

    :param root: The project's root folder
    :param key: The hash identifier of the cue to load
    :return: The cue identified by the specified hash
    """

    if key in __LOAD_STACK:
        raise CircularReferenceException({
            'message': ("The Cue identified by id {0} has already been partially loaded but was referenced again. "
                        "This is a circular reference").format(key),
            'key': key
        })

    __LOAD_STACK.append(key)

    if key in __CUE_CACHE:
        logger.debug("Loading {0} from cue cache".format(key))
        ret = __CUE_CACHE[key]
        __LOAD_STACK.pop()
        return ret

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
        ret = AudioCue(project=project).load(root, key, j)
    elif t == 'control':
        ret = ControlCue(project=project, target=None, target_volume=0.0, fade_duration=0,
                         stop_target_on_volume_reached=True).load(root, key, j)
    else:
        logger.warning("Unknown cue type or missing plugin for type {0}".format(t))
        ret = Cue(project=project).load(root, key, j)

    __LOAD_STACK.pop()
    __CUE_CACHE[key] = ret
    return ret


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

        self.__update_listeners = {}
        for cue in self.__cues:
            i = self.__cues.index(cue)
            self.__connect_callback(i, cue)

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
        self.__connect_callback(key, value)

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
        i = self.__cues.index(other)
        self.__connect_callback(i, other)

        return self

    def __isub__(self, other):
        if not isinstance(other, Cue):
            raise TypeError("Cannot add type {0} to CueList".format(type(other)))

        i = self.__cues.index(other)
        self.__cues.remove(other)
        self.__disconnect_callback(other)
        self.emit('changed', i, CueStackChangeType.DELETE)
        return self

    def __connect_callback(self, i, cue):
        update_id = cue.connect('update', lambda *x: self.emit(
            'changed', i, CueStackChangeType.UPDATE
        ))
        self.__update_listeners[cue] = update_id

    def __disconnect_callback(self, cue):
        cue.disconnect(self.__update_listeners[cue])
        del self.__update_listeners[cue]

    def index(self, obj):
        return self.__cues.index(obj)

    def get_cue_relative_to(self, cue, rel):
        return self.__cues.index(cue) + rel

    def add_cue_relative_to(self, existing, cue):
        i = self.index(existing)+1
        self.__cues.insert(i, cue)
        self.__connect_callback(i, cue)
        self.emit('changed', i, CueStackChangeType.INSERT)

    def remove_cue(self, cue):
        i = self.__cues.index(cue)
        self.__cues.remove(cue)
        self.__disconnect_callback(cue)
        self.emit('changed', i, CueStackChangeType.DELETE)

    @staticmethod
    def load(root, key, project):
        j = read(root, key)

        name = util.pick(j, 'name', "Untitled Cue Stack")
        current_hash = key
        last_hash = util.pick(j, 'previousRevision', None)
        cues = []
        if 'cues' in j:
            for cue in j['cues']:
                c = load_cue(root, cue, project)
                logger.debug("Loaded {0}".format(repr(c)))
                cues.append(c)
        else:
            logger.error("Bad Cue Stack: No 'cues' object!")

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

    def try_seek_all(self, ms):
        for cue in [c for c in self.__cues if c.state is not PlaybackState.STOPPED and isinstance(c, AudioCue)]:
            cue.seek(ms)

    def resume_all(self, fade=0):
        for cue in [c for c in self.__cues if c.state is PlaybackState.PAUSED]:
            cue.action()

    def pause_all(self, fade=0):
        for cue in [c for c in self.__cues if c.state is PlaybackState.PLAYING and isinstance(c, AudioCue)]:
            cue.pause()

    def stop_all(self, fade=0):
        for cue in self.__cues:
            cue.stop(fade=fade)