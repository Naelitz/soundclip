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
gi.require_version('Gst', '1.0')

import logging
logger = logging.getLogger('SoundClip')

from gi.repository import GObject, Gst


def FADE_LINEAR(initial_vol, target_vol, start, duration, now, user_args):
    # Linear fade curve (Y = (M * (X - X_1))/Y_1)
    return (((target_vol - initial_vol) / duration) * (now - start)) + initial_vol, now < start + duration


class PlaybackController(GObject.Object):

    __gsignals__ = {
        'playback-state-changed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT, )),
    }

    def __init__(self, source, target_volume=1.0, **properties):
        super().__init__(**properties)

        logger.debug("Initializing to source {0}".format(source))
        self.__source = source

        self.__fading = False
        self.__fade_func = FADE_LINEAR
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

        self.__playbin = Gst.ElementFactory.make('playbin', None)
        fs = Gst.ElementFactory.make('fakesink', None)
        self.__playbin.set_property('video-sink', fs)
        self.__playbin.set_property('uri', self.__source)

        self.__pipeline.add(self.__playbin)
        # self.__pipeline.get_clock().get_time()
        self.__clock_id = self.__pipeline.get_clock().new_periodic_id(0, 100000000)
        Gst.Clock.id_wait_async(self.__clock_id, self.tick, None)
        self.__last_update_time = 0

    def __del__(self):
        self.__pipeline.set_state(Gst.State.NULL)
        Gst.Clock.id_unschedule(self.__clock_id)

    def reset(self):
        logger.debug("Playback Controller Reset")
        self.__pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)
        self.__pipeline.set_state(Gst.State.READY)

    def preroll(self):
        logger.debug("Playback Controller preroll")
        self.__pipeline.set_state(Gst.State.PAUSED)

    def play(self, volume=0.1, fade=0):
        logger.debug("Playback Controller play")

        if fade > 0:
            self.__fade_start_time = -1
            self.__fade_duration = fade
            self.__fade_start_vol = 0.0
            self.__playbin.set_property('volume', 0.0)
            self.__fade_complete_func = None
            self.__fading = True
        else:
            self.__playbin.set_property('volume', volume)
            self.__fade_target_volume = volume

        self.__pipeline.set_state(Gst.State.PLAYING)

    def pause(self, fade=0):
        logger.debug("Playback Controller Pause")

        if fade > 0:
            self.__fade_start_time = -1
            self.__fade_duration = fade
            self.__fade_start_vol = self.__playbin.get_property('volume')
            self.__fade_target_volume = 0.0
            self.__fade_complete_func = lambda: self.__pipeline.set_state(Gst.State.PAUSED)
            self.__fading = True
        else:
            self.__pipeline.set_state(Gst.State.PAUSED)

    def stop(self, fade=0):
        logger.debug("Playback Controller Stop Initiated (fade={0})".format(fade))

        if fade > 0:
            self.__fade_start_time = -1
            self.__fade_duration = fade
            self.__fade_start_vol = self.__playbin.get_property('volume')
            self.__fade_target_volume = 0.0
            self.__fade_complete_func = self.__stop
            self.__fading = True
        else:
            self.__stop()

    def __stop(self):
        logger.debug("Playback stopped")
        self.__pipeline.set_state(Gst.State.NULL)
        self.reset()

    def on_eos(self, bus, message):
        logger.info("Playback Finished [EOS] for {0}".format(self.__source))
        self.reset()

    def on_error(self, bus, message):
        logger.error("GStreamer playback error: {0}".format(message.parse_error()))

    def get_position(self):
        return int(self.__pipeline.query_position(Gst.Format.TIME)[0] / Gst.MSECOND)

    def get_duration(self):
        return int(self.__pipeline.query_duration(Gst.Format.TIME)[0] / Gst.MSECOND)

    @property
    def playing(self):
        return Gst.State.PLAYING in self.__pipeline.get_state(Gst.CLOCK_TIME_NONE)

    @property
    def paused(self):
        return Gst.State.PAUSED in self.__pipeline.get_state(Gst.CLOCK_TIME_NONE)

    @property
    def stopped(self):
        return not self.playing and not self.paused

    def tick(self, clock, time, id, user_data):
        if self.__fading:
            # Adjust volume according to fade curve
            if self.__fade_start_time == -1:
                self.__fade_start_time = time

            v, cont = self.__fade_func(self.__fade_start_vol, self.__fade_target_volume,
                                       int(self.__fade_start_time), int(self.__fade_duration * Gst.MSECOND),
                                       time, self.__fade_func_args) \
                if callable(self.__fade_func) else self.__fade_target_volume

            # Clamp result
            if self.__fade_start_vol < self.__fade_target_volume <= v:
                logger.debug("CLAMPING: Higher than target volume")
                v = self.__fade_target_volume
                self.__fading = False
            elif self.__fade_start_time > self.__fade_target_volume >= v:
                logger.debug("CLAMPING: Lower than target volume")
                v = self.__fade_target_volume
                self.__fading = False
            elif not cont:
                logger.debug("CLAMPING: Fade Function asked to stop")
                v = self.__fade_target_volume
                self.__fading = False

            if v > 0.1:
                self.__fading = False
                v = 0.1
                logger.warning("SPEAKER PROTECTION: Something's wrong with the fade curve")

            # Apply Volume Change
            self.__playbin.set_property('volume', v)

            # If we're done fading, run callback
            if not self.__fading and callable(self.__fade_complete_func):
                self.__fade_complete_func()
        self.__last_update_time = time