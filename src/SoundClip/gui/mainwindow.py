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
from SoundClip.gui.containers import SCCueListContainer, SCActiveCueList
from SoundClip.gui.menu import SCHeaderBar
from SoundClip.project import Project


class SCMainWindow(Gtk.Window):
    """
    The main window for SoundClip.
    """

    def __init__(self, project=None, **properties):
        super().__init__(**properties)

        self.title_bar = SCHeaderBar(self)
        self.set_titlebar(self.title_bar)

        self.__grid = Gtk.Grid()
        self.add(self.__grid)

        # TODO: Current cue name, description, notes, and go button

        self.__cue_lists = SCCueListContainer(self)
        self.__grid.attach(self.__cue_lists, 0, 0, 7, 1)

        self.__active_cues = SCActiveCueList()
        self.__grid.attach(self.__active_cues, 7, 0, 3, 1)

        self.project = Project() if project is None else project
        self.change_project(self.project)

        self.set_size_request(800, 600)
        self.connect("delete-event", Gtk.main_quit)

    def change_project(self, p: Project):
        if self.project is not None:
            self.project.close()
        self.project = p

        self.__cue_lists.on_project_changed(self.project)

        self.title_bar.set_subtitle(("*" if not p.root else "") + p.name)
        pass

    def send_stop_all(self):
        self.__cue_lists.send_stop_all()

    def toggle_workspace_lock(self, button):
        print("TODO: TOGGLE_LOCK_WORKSPACE")