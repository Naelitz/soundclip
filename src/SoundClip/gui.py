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
from SoundClip import __version__
from SoundClip.project import Project


class SCHeaderBar(Gtk.HeaderBar):
    """
    SoundClip's custom headerbar
    """

    def __init__(self, **properties):
        super().__init__(**properties)

        self.set_title("SoundClip " + __version__)
        self.set_subtitle("Unknown Project")
        self.set_show_close_button(True)


class SCMainWindow(Gtk.Window):
    """
    The main window for SoundClip.
    """

    def __init__(self, **properties):
        super().__init__(**properties)

        self.title_bar = SCHeaderBar()
        self.set_titlebar(self.title_bar)

        self.project = None
        self.change_project(Project())

        self.set_size_request(800, 600)
        self.connect("delete-event", Gtk.main_quit)

    def change_project(self, p: Project):
        if self.project is not None:
            self.project.close()
        self.project = p

        self.title_bar.set_subtitle(("*" if not p.root else "") + p.name)
        pass