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


class PlaybackController(GObject.Object):

    __gsignals__ = {
        'playback-state-changed': (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT, ))
    }

    def __init__(self, source):
        logger.debug("Initializing to source {0}".format(source))
        self.__source = source

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

    def reset(self):
        logger.debug("Playback Controller Reset")
        self.__pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)
        self.__pipeline.set_state(Gst.State.READY)

    def preroll(self):
        logger.debug("Playback Controller preroll")
        self.__pipeline.set_state(Gst.State.PAUSED)

    def play(self):
        logger.debug("Playback Controller play")
        self.__pipeline.set_state(Gst.State.PLAYING)

    def pause(self):
        logger.debug("Playback Controller Pause")
        self.__pipeline.set_state(Gst.State.PAUSED)

    def stop(self):
        logger.debug("Playback Controller Stop")
        self.__pipeline.set_state(Gst.State.NULL)
        self.reset()

    def on_eos(self, bus, message):
        logger.info("Playback Finished [EOS] for {0}".format(self.__source))
        self.reset()

    def on_error(self, bus, message):
        logger.error("GStreamer playback error: {0}".format(message.parse_error()))

    def get_position(self):
        return self.__pipeline.query_position(Gst.Format.TIME) / Gst.MSECOND

    def get_duration(self):
        return self.__pipeline.query_duration(Gst.Format.TIME) / Gst.MSECOND

    @property
    def playing(self):
        return self.__pipeline.get_state(Gst.CLOCK_TIME_NONE) == Gst.State.PLAYING

    @property
    def paused(self):
        return self.__pipeline.get_state(Gst.CLOCK_TIME_NONE) == Gst.State.PAUSED

    @property
    def stopped(self):
        return not self.playing and not self.paused