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

import logging
logger = logging.getLogger('SoundClip')

from gi.repository import GObject, Gtk

from SoundClip import __version__
from SoundClip.gui.containers import SCCueListContainer
from SoundClip.gui.menu import SCHeaderBar
from SoundClip.project import Project


class SCMainWindow(Gtk.Window):
    """
    The main window for SoundClip.
    """

    __gsignals__ = {
        'lock-toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool, ))
    }

    def __init__(self, project=None, **properties):
        super().__init__(**properties)

        self.title_bar = SCHeaderBar(self)
        self.set_titlebar(self.title_bar)

        # TODO: Current cue name, description, notes, and go button?

        self.__cue_lists = SCCueListContainer(self)
        self.add(self.__cue_lists)

        self.__project = Project() if project is None else project
        self.change_project(self.__project)

        self.set_size_request(800, 600)
        self.connect("delete-event", Gtk.main_quit)

        self.__locked = False

    def change_project(self, p: Project):
        if self.__project is not None:
            self.__project.close()
        self.__project = p

        self.__cue_lists.on_project_changed(self.__project)

        self.update_title()

    def update_title(self):
        if not self.__project.root:
            self.title_bar.set_title("SoundClip " + __version__)
            self.title_bar.set_subtitle(("*" if not self.__project.root else "") + self.__project.name)
        else:
            self.title_bar.set_title(self.__project.name)
            self.title_bar.set_subtitle(self.__project.root)

    @property
    def project(self):
        return self.__project

    def send_stop_all(self):
        for stack in self.__project.cue_stacks:
            stack.stop_all()

    def toggle_workspace_lock(self, button):
        self.__locked = not self.__locked
        self.emit('lock-toggled', self.__locked)

    @property
    def locked(self):
        return self.__locked

    def get_selected_cue(self):
        return self.__cue_lists.get_selected_cue()

    def add_cue_relative_to(self, existing, cue):
        stack = self.__cue_lists.get_current_stack()
        if existing:
            stack.add_cue_relative_to(existing, cue)
        else:
            stack += cue