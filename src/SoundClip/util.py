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

import hashlib
import datetime
import os
from gi.repository import GLib, Gtk, GObject


class Timer(GObject.Object):

    __gsignals__ = {
        'expired': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'update': (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_LONG,))
    }

    def __init__(self, duration, resolution=50):
        super().__init__()

        self.__duration = duration
        self.__resolution = resolution
        self.__start_time = -1

    def fire(self):
        self.__start_time = now()
        GLib.timeout_add(self.__resolution, self.tick)

    def tick(self):
        current_time = now()

        more = current_time < self.__start_time + self.__duration

        if more:
            self.emit('update', current_time-self.__start_time)
        else:
            self.emit('expired')

        return more
GObject.type_register(Timer)


def timepart(ms):
    ss, ms = divmod(ms, 1000)
    mm, ss = divmod(ss, 60)
    return mm, ss, ms


def timefmt(ms):
    mm, ss, ms = timepart(ms)
    return "{:02d}:{:05.2f}".format(mm, ss + ms/1000)


def sha(s: str):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def get_gtk_version():
    return str(Gtk.get_major_version()) + "." + str(Gtk.get_minor_version()) + "." + str(Gtk.get_micro_version())


def now():
    t = datetime.datetime.now()
    return (t.day * 24 * 60 * 60 + t.second) * 1000 + t.microsecond / 1000.0


def pick(d, key, default):
    return d[key] if key in d else default


def in_directory(file, directory):
    """
    See http://stackoverflow.com/q/3812849/1200316

    :param file:
    :param directory:
    :return: Whether or not the specified file is in the specified directory
    """

    # make both absolute
    directory = os.path.join(os.path.realpath(directory), '')
    file = os.path.realpath(file)

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([file, directory]) == directory