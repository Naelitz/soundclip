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


class CueDialog(Gtk.Dialog):
    def __init__(self, w, c, **properties):
        super().init("Cue Editor", w, 0,
                     (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK), **properties)

        self.__main_window = w
        self.__cue = c
        self.__editor = self.__cue.get_editor()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # TODO: Common Cue Editor

        box.add(self.__editor)

        self.get_content_area().add(box)
        self.set_modal(True)

    def get_custom_editor(self):
        return self.__editor

    def get_cue(self):
        return self.__cue