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
from gi.repository import Gtk


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