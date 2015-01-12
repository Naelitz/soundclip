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
from SoundClip.gui.cuelist import SCCueList


class SCCueListContainer(Gtk.Notebook):
    """
    A container of all cue lists for this production
    """

    def __init__(self, w, **properties):
        super().__init__(**properties)
        self.__main_window = w
        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_vexpand(True)
        self.set_valign(Gtk.Align.FILL)

    def on_project_changed(self, p):
        for stack in p.cue_stacks:
            self.append_page(SCCueList(self.__main_window, stack), Gtk.Label(stack.name))
        self.set_show_tabs(True if self.get_n_pages() > 1 else False)

    def get_selected_cue(self):
        self.get_nth_page(self.get_current_page()).get_selected()

    def get_current_stack(self):
        return self.get_nth_page(self.get_current_page()).get_stack()