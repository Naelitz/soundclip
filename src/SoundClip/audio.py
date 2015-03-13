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

import gi
from SoundClip import util
from SoundClip.util import now

gi.require_version('Gst', '1.0')

import logging
logger = logging.getLogger('SoundClip')

from gi.repository import GLib, GObject, Gst, GstPbutils


def fade_curve_linear(initial_vol, target_vol, start, duration, now, user_args):
    # Linear fade curve (Y = (M * (X - X_1))/Y_1)
    return (((target_vol - initial_vol) / duration) * (now - start)) + initial_vol, now < start + duration

# TODO: Cubic and Bezier Fade Curves


class PlaybackController(GObject.Object):
    """
    Playback Controller for Audio Cues. Serves as a bridge between the cue and gstreamer.

    # TODO: One pipeline for the whole program? Multiple volume sliders show up in gnome...

    uridecodebin -> audioconvert -> volume -> autoaudiosink
    """

    discoverer = None

    @staticmethod
    def __setup_discoverer():
        if PlaybackController.discoverer is None:
            PlaybackController.discoverer = GstPbutils.Discoverer()

    @staticmethod
    def is_file_supported(uri):
        PlaybackController.__setup_discoverer()

        try:
            file = PlaybackController.discoverer.discover_uri("file://" + uri)
            return len(file.get_audio_streams()) > 0
        except GLib.Error as ex:
            logger.warning("Cannot play audio file: {0}".format(ex.message))
            return False

    __gsignals__ = {
        'playback-state-changed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT, )),
        'tick': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, source, target_volume=1.0, **properties):
        super().__init__(**properties)

        logger.debug("Initializing to source {0}".format(source))
        self.__source = source

        self.__fading = False
        self.__fade_func = fade_curve_linear
        self.__fade_func_args = {}
        self.__fade_start_time = 0
        self.__fade_duration = 0
        self.__fade_start_vol = 0
        self.__fade_target_volume = max(min(target_volume, 10.0), 0.0)
        self.__fade_complete_func = None

        self.__pipeline = Gst.Pipeline()

        self.__bus = self.__pipeline.get_bus()
        self.__bus.add_signal_watch()
        self.__bus.connect('message::eos', self.on_eos)
        self.__bus.connect('message::error', self.on_error)

        self.__dec = Gst.ElementFactory.make('uridecodebin', None)
        self.__dec.set_property('uri', self.__source)
        self.__dec.connect('pad-added', self.__on_decoded_pad)
        self.__dec.connect('drained', lambda *x: GLib.idle_add(self.on_drained))
        self.__conv = Gst.ElementFactory.make('audioconvert', None)
        self.__conv_sink = self.__conv.get_static_pad('sink')
        self.__vol = Gst.ElementFactory.make('volume', None)
        self.__sink = Gst.ElementFactory.make('autoaudiosink', None)

        self.__pipeline.add(self.__dec)
        self.__pipeline.add(self.__conv)
        self.__pipeline.add(self.__vol)
        self.__pipeline.add(self.__sink)

        self.__conv.link(self.__vol)
        self.__vol.link(self.__sink)

        if PlaybackController.discoverer is None:
            PlaybackController.__setup_discoverer()

        dur = int(PlaybackController.discoverer.discover_uri(source).get_duration() / Gst.MSECOND)
        logger.debug("Discovered length {0}".format(util.timefmt(dur)))
        self.__duration = dur

        # Schedule a tick on 50ms interval
        self.__active = True
        GLib.timeout_add(50, self.tick)
        self.__last_update_time = 0

    def __del__(self):
        self.__pipeline.set_state(Gst.State.NULL)
        self.__active = False

    def __on_decoded_pad(self, element, pad):
        name = pad.query_caps(None).to_string()
        if name.startswith("audio/") and not self.__conv_sink.is_linked():
            logger.debug("Linking Pad: {0}".format(name))
            pad.link(self.__conv_sink)

    def reset(self):
        logger.debug("Playback Controller Reset")
        self.__pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)
        self.__pipeline.set_state(Gst.State.READY)

    def preroll(self):
        logger.debug("Playback Controller preroll")
        self.__pipeline.set_state(Gst.State.PAUSED)
        self.__pipeline.get_state(Gst.CLOCK_TIME_NONE)
        self.__duration = self.__duration if self.__duration > 0 else \
            int(self.__pipeline.query_duration(Gst.Format.TIME)[1] / Gst.MSECOND)

    def play(self, volume=1.0, fade=0):
        logger.debug("Playback Controller play ({0})".format("Fade={0}".format(fade) if fade > 0 else "Not Fading"))

        if fade > 0:
            self.__vol.set_property('volume', 0.0)
            self.fade_to(volume, fade)
        else:
            self.__vol.set_property('volume', volume)
            self.__fade_target_volume = volume
            self.__fading = False

        self.__pipeline.set_state(Gst.State.PLAYING)

    def pause(self, fade=0):
        logger.debug("Playback Controller Pause")
        if fade > 0:
            self.fade_to(0.0, fade, lambda *x: self.__pipeline.set_state(Gst.State.PAUSED))
        else:
            self.__pipeline.set_state(Gst.State.PAUSED)

    def stop(self, fade=0):
        logger.debug("Playback Controller Stop Initiated (fade={0})".format(fade))
        self.fade_to(0.0, fade, self.__stop) if fade > 0 else self.__stop()

    def fade_to(self, target_volume, duration, callback=None):
        if duration <= 0:
            logger.warning("Asked to fade but fade duration was zero!")
            self.set_volume(target_volume)
            if callable(callback):
                callback()
            return

        self.__fade_start_time = -1
        self.__fade_duration = duration
        self.__fade_start_vol = self.volume
        self.__fade_target_volume = target_volume
        self.__fade_complete_func = callback

        logger.debug("Asked to fade from {0:.2f} to {1:.2f} over {2}ms".format(
            self.__fade_start_vol, target_volume, duration
        ))
        self.__fading = True

    @property
    def volume(self):
        return self.__vol.get_property('volume')

    def set_volume(self, target, fade=0):
        if fade > 0:
            self.fade_to(target, fade, None)
        else:
            self.__vol.set_property('volume', target)

    def __stop(self):
        logger.debug("Playback stopped")
        self.__pipeline.set_state(Gst.State.NULL)
        self.reset()

    def on_eos(self, bus, message):
        logger.info("Playback Finished [EOS] for {0}".format(self.__source))
        self.reset()

    def on_drained(self):
        logger.debug("URIDecodeBin Drained")
        self.on_eos(None, None)
        return False

    def on_error(self, bus, message):
        logger.error("GStreamer playback error: {0}".format(message.parse_error()))

    def get_position(self):
        return int(self.__pipeline.query_position(Gst.Format.TIME)[1] / Gst.MSECOND)

    def get_duration(self):
        return self.__duration

    def __pipeline_state(self, timeout=Gst.CLOCK_TIME_NONE):
        return self.__pipeline.get_state(timeout)

    def is_pipeline_in_state(self, state, default_on_fail=False):
        ok, pipeline_state, pending = self.__pipeline_state()

        if ok == Gst.StateChangeReturn.ASYNC:
            return pending == state
        elif ok == Gst.StateChangeReturn.SUCCESS:
            return pipeline_state == state
        else:
            return default_on_fail

    @property
    def playing(self):
        return self.is_pipeline_in_state(Gst.State.PLAYING)

    @property
    def paused(self):
        return self.is_pipeline_in_state(Gst.State.PAUSED)

    @property
    def stopped(self):
        return not self.playing and not self.paused

    def tick(self):
        if self.playing or self.paused:
            if self.__fading:
                # Adjust volume according to fade curve
                if self.__fade_start_time == -1:
                    self.__fade_start_time = now()

                current_time = now()

                v, cont = self.__fade_func(self.__fade_start_vol, self.__fade_target_volume,
                                           int(self.__fade_start_time), int(self.__fade_duration),
                                           current_time, self.__fade_func_args) \
                    if callable(self.__fade_func) else self.__fade_target_volume

                logger.debug("Fade Curve returned target volume {0}. Continuing: {1}".format(v, cont))

                # Clamp result
                if self.__fade_start_vol < self.__fade_target_volume <= v:
                    logger.debug("CLAMPING: Higher than target volume")
                    v = self.__fade_target_volume
                    self.__fading = False
                elif self.__fade_start_vol > self.__fade_target_volume >= v:
                    logger.debug("CLAMPING: Lower than target volume")
                    v = self.__fade_target_volume
                    self.__fading = False
                elif not cont:
                    logger.debug("CLAMPING: Fade Function asked to stop")
                    v = self.__fade_target_volume
                    self.__fading = False

                # Apply Volume Change
                self.__vol.set_property('volume', v)

                # If we're done fading, run callback
                if not self.__fading and callable(self.__fade_complete_func):
                    self.__fade_complete_func()
            self.emit('tick')
        self.__last_update_time = now()
        return self.__active