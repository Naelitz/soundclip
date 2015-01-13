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
from gi.repository import Gtk, Gdk


class SCCueDialog(Gtk.Dialog):
    def __init__(self, w, c, **properties):
        super().__init__("Cue Editor{0}".format(" - {0}".format(c.name) if c else ""), w, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK), **properties)

        self.__main_window = w
        self.__cue = c
        self.__editor = self.__cue.get_editor()

        grid = Gtk.Grid()

        # TODO: Common Cue Editor
        name_label = Gtk.Label("Name")
        name_label.set_halign(Gtk.Align.END)
        grid.attach(name_label, 0, 0, 1, 1)
        self.__name = Gtk.Entry()
        self.__name.set_text(self.__cue.name)
        self.__name.set_hexpand(True)
        self.__name.set_halign(Gtk.Align.FILL)
        grid.attach(self.__name, 1, 0, 1, 1)

        desc_label = Gtk.Label("Description")
        desc_label.set_halign(Gtk.Align.END)
        grid.attach(desc_label, 0, 1, 1, 1)
        self.__description = Gtk.Entry()
        self.__description.set_text(self.__cue.description)
        self.__description.set_hexpand(True)
        self.__description.set_halign(Gtk.Align.FILL)
        grid.attach(self.__description, 1, 1, 1, 1)

        notes_label = Gtk.Label("Notes")
        notes_label.set_halign(Gtk.Align.END)
        grid.attach(notes_label, 0, 2, 1, 1)
        self.__notes = Gtk.Entry()
        self.__notes.set_text(self.__cue.notes)
        self.__notes.set_hexpand(True)
        self.__notes.set_halign(Gtk.Align.FILL)
        grid.attach(self.__notes, 1, 2, 1, 1)

        prew_label = Gtk.Label("Pre-Wait Time")
        prew_label.set_halign(Gtk.Align.END)
        grid.attach(prew_label, 0, 3, 1, 1)
        self.__prewait = Gtk.Entry()
        self.__prewait.set_text(str(self.__cue.pre_wait)) # TODO: Time Picker
        self.__prewait.set_hexpand(True)
        self.__prewait.set_halign(Gtk.Align.FILL)
        grid.attach(self.__prewait, 1, 3, 1, 1)

        postw_label = Gtk.Label("Post-Wait Time")
        postw_label.set_halign(Gtk.Align.END)
        grid.attach(postw_label, 0, 4, 1, 1)
        self.__postwait = Gtk.Entry()
        self.__postwait.set_text(str(self.__cue.post_wait))
        self.__postwait.set_hexpand(True)
        self.__postwait.set_halign(Gtk.Align.FILL)
        grid.attach(self.__postwait, 1, 4, 1, 1) # TODO: Time Picker

        if self.__editor:
            wrapper = Gtk.ScrolledWindow()
            wrapper.add(self.__editor)
            wrapper.set_hexpand(True)
            wrapper.set_halign(Gtk.Align.FILL)
            wrapper.set_vexpand(True)
            wrapper.set_valign(Gtk.Align.FILL)
            grid.attach(wrapper, 0, 5, 2, 1)

        self.get_content_area().pack_start(grid, True, True, 0)
        self.set_modal(True)
        w, h = self.__main_window.get_size()
        g = Gdk.Geometry()
        g.min_width = int(float(w) * .7)
        g.max_width = int(float(w) * .7)
        g.max_height = int(float(h) * .7)
        self.set_geometry_hints(None, g, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
        self.connect('response', self.on_response)
        self.show_all()

    def get_custom_editor(self):
        return self.__editor

    def get_cue(self):
        return self.__cue

    def on_response(self, w, id):
        if id == Gtk.ResponseType.OK:
            self.__cue.name = self.__name.get_text().strip()
            self.__cue.description = self.__description.get_text().strip()
            self.__cue.notes = self.__notes.get_text().strip()
            self.__cue.pre_wait = float(self.__prewait.get_text())
            self.__cue.post_wait = float(self.__postwait.get_text())

            self.__cue.on_editor_closed(self.__editor)