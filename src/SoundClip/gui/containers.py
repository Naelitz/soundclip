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
from SoundClip.cue import PlaybackActionType
from SoundClip.gui.cuelist import SCCueList


class SCActiveCueList(Gtk.Box):
    """
    A list displaying cues that are currently running, including duration, volume, and progress

    TODO: Make hideable via a Revealer and/or popout to separate window, 'No Active Cues' needs to be centered
    """

    def __init__(self, **properties):
        super().__init__(**properties)
        self.__active_cues = []
        self.__no_active_cues_label = Gtk.Label("No Active Cues")
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.add(self.__no_active_cues_label)

    def on_cue_playback_update(self, cue, action):
        if action is PlaybackActionType.STOP:
            self.__active_cues.remove(cue)
        elif cue not in self.__active_cues:
            if len(self.__active_cues) == 0:
                self.remove(self.__no_active_cues_label)
            self.__active_cues.insert(0, cue)

        if len(self.__active_cues) == 0:
            self.add(self.__no_active_cues_label)


class SCCueListContainer(Gtk.Notebook):
    """
    A container of all cue lists for this production
    """

    def __init__(self, w, **properties):
        super().__init__(**properties)
        self.__main_window = w

    def on_project_changed(self, p):
        for stack in p.cue_stacks:
            self.append_page(SCCueList(stack), Gtk.Label(stack.name))
        self.set_show_tabs(True if self.get_n_pages() > 1 else False)

    def send_stop_all(self):
        pass