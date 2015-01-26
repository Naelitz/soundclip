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

from gi.repository import Gtk

from SoundClip import util


class TimePicker(Gtk.Box):
    def __init__(self, initial_milliseconds=0, **properties):
        super().__init__(**properties)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        mm, ss, ms = util.timepart(initial_milliseconds)

        self.__minute_adjustment = Gtk.Adjustment(0, 0, step_increment=1, page_increment=1, page_size=1)
        self.__minute_button = Gtk.SpinButton()
        self.__minute_button.set_adjustment(self.__minute_adjustment)
        self.__minute_button.set_value(mm)
        self.pack_start(self.__minute_button, True, True, 0)
        self.pack_start(Gtk.Label("minutes, "), False, False, 5)

        self.__second_adjustment = Gtk.Adjustment(0, 0, 59, 1, 1, 1)
        self.__second_button = Gtk.SpinButton()
        self.__second_button.set_adjustment(self.__second_adjustment)
        self.__second_button.set_value(ss)
        self.pack_start(self.__second_button, True, True, 0)
        self.pack_start(Gtk.Label("seconds, "), False, False, 5)

        self.__millisecond_adjustment = Gtk.Adjustment(0, 0, 999, 1, 1, 1)
        self.__millisecond_button = Gtk.SpinButton()
        self.__millisecond_button.set_adjustment(self.__millisecond_adjustment)
        self.__millisecond_button.set_value(ms)
        self.pack_start(self.__millisecond_button, True, True, 0)
        self.pack_start(Gtk.Label("milliseconds"), False, False, 5)

    def get_minutes(self):
        return self.__minute_button.get_value_as_int()

    def get_seconds(self):
        return self.__second_button.get_value_as_int()

    def get_milliseconds(self):
        return self.__millisecond_button.get_value_as_int()

    def get_total_milliseconds(self):
        return (self.get_minutes() * 60 + self.get_seconds()) * 1000 + self.get_milliseconds()