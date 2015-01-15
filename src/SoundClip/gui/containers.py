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
from SoundClip.project import StackChangeAction

logger = logging.getLogger('SoundClip')

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

        self.__project = None
        self.__cbid = None

    def update_show_tabs(self):
        self.set_show_tabs(True if self.get_n_pages() > 1 else False)

    def on_project_changed(self, p):
        if self.__project is not None and self.__cbid is not None:
            logger.debug("Disconnecting callbacks from previous project")
            self.__project.disconnect(self.__cbid)

        self.__project = p
        self.__cbid = self.__project.connect('stack-changed', self.on_stacks_changed)

        for i in range(0, self.get_n_pages()):
            self.remove_page(-1)
        for stack in p.cue_stacks:
            stack_container = SCCueList(self.__main_window, stack)
            self.append_page(stack_container, stack_container.get_title_widget())
        self.update_show_tabs()
        self.show_all()

    def on_stacks_changed(self, obj, key, action):
        logger.debug("Stack Changed: {0}, Action: {1}".format(key, action))
        if action is StackChangeAction.INSERT:
            stack_container = SCCueList(self.__main_window, self.__main_window.project[key])
            self.append_page(stack_container, stack_container.get_title_widget())
        elif action is StackChangeAction.DELETE:
            self.remove_page(key)
        self.update_show_tabs()
        self.show_all()

    def get_selected_cue(self):
        self.get_nth_page(self.get_current_page()).get_selected()

    def get_current_stack(self):
        return self.get_nth_page(self.get_current_page()).get_stack()