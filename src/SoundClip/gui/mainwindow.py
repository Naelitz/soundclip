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
from SoundClip.gui.widgets import TransportControls
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

        grid = Gtk.Grid()

        self.__cue_lists = SCCueListContainer(self)
        grid.attach(self.__cue_lists, 0, 0, 1, 1)

        self.__transport_controls = TransportControls(self)
        grid.attach(self.__transport_controls, 0, 1, 1, 1)

        self.add(grid)

        self.__project = None
        self.change_project(Project() if project is None else project)

        self.set_size_request(800, 600)
        self.connect("delete-event", self.on_close)

        self.__locked = False

    def on_close(self, *args):
        self.project.close()
        Gtk.main_quit(*args)

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

    def update_notes(self, cue):
        self.__transport_controls.set_notes(cue.notes)

    def refocus_cuelist(self):
        self.__cue_lists.get_nth_page(self.__cue_lists.get_current_page()).refocus()

    @property
    def project(self):
        return self.__project

    def try_seek_all(self, ms):
        for stack in self.__project.cue_stacks:
            stack.try_seek_all(ms)

    def send_pause_all(self, fade=0):
        for stack in self.__project.cue_stacks:
            stack.pause_all(fade=fade)

    def send_resume_all(self, fade=0):
        for stack in self.__project.cue_stacks:
            stack.resume_all(fade=fade)

    def send_stop_all(self, fade=0):
        for stack in self.__project.cue_stacks:
            stack.stop_all(fade=fade)

    def toggle_workspace_lock(self, button):
        self.__locked = not self.__locked
        self.emit('lock-toggled', self.__locked)

    @property
    def locked(self):
        return self.__locked

    def get_selected_cue(self):
        return self.__cue_lists.get_selected_cue()

    def get_current_cue_stack(self):
        return self.__cue_lists.get_current_stack()

    def add_cue_relative_to(self, existing, cue):
        stack = self.get_current_cue_stack()
        if existing:
            stack.add_cue_relative_to(existing, cue)
        else:
            stack += cue