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

import SoundClip
from SoundClip.gui.widgets import TimePicker
from SoundClip.util import get_gtk_version
from gi.repository import Gtk, Gdk, Gst


class SCAboutDialog(Gtk.AboutDialog):
    def __init__(self, w, **properties):
        super().__init__(**properties)
        self.set_transient_for(w)
        self.set_modal(True)
        self.set_program_name("SoundClip")
        self.set_version("Version {0}\nGtk: {1}\n{2}".format(
            SoundClip.__version__,
            get_gtk_version(),
            Gst.version_string()
        ))
        self.set_license_type(Gtk.License.GPL_3_0)
        self.set_copyright("Copyright \xa9 2014-2015 Nathan Lowe")
        self.set_website("https://github.com/techwiz24/soundclip")
        self.set_website_label("https://github.com/techwiz24/soundclip")


class SCRenameCueListDialog(Gtk.Dialog):
    def __init__(self, w, name, **properties):
        super().__init__("Rename CueList - {0}".format(name), w, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK), **properties)
        self.__main_window = w
        grid = Gtk.Grid()
        grid.attach(Gtk.Label("Name:"), 0, 0, 1, 1)

        self.__name = Gtk.Entry()
        self.__name.set_text(name)
        self.__name.set_hexpand(True)
        self.__name.set_halign(Gtk.Align.FILL)
        grid.attach(self.__name, 1, 0, 1, 1)

        self.get_content_area().pack_start(grid, True, True, 0)
        self.set_modal(True)
        w, h = self.__main_window.get_size()
        g = Gdk.Geometry()
        g.min_width = int(float(w) * .7)
        g.max_width = int(float(w) * .7)
        g.max_height = int(float(h) * .7)
        self.set_geometry_hints(None, g, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
        self.show_all()

    def get_name(self):
        return self.__name.get_text()


class SCProjectPropertiesDialog(Gtk.Dialog):
    def __init__(self, w, **properties):
        super().__init__("Project Properties - {0}".format(w.project.name), w, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK), **properties)

        self.__main_window = w
        grid = Gtk.Grid()

        stats_label = Gtk.Label("{0:g} cues in {1:g} lists".format(
            sum([len(stack) for stack in self.__main_window.project.cue_stacks]),
            len(self.__main_window.project.cue_stacks))
        )
        stats_label.set_halign(Gtk.Align.CENTER)
        grid.attach(stats_label, 0, 0, 3, 1)

        name_label = Gtk.Label("Name")
        name_label.set_halign(Gtk.Align.END)
        grid.attach(name_label, 0, 1, 1, 1)
        self.__name = Gtk.Entry()
        self.__name.set_text(self.__main_window.project.name)
        self.__name.set_hexpand(True)
        self.__name.set_halign(Gtk.Align.FILL)
        grid.attach(self.__name, 1, 1, 2, 1)

        creator_label = Gtk.Label("Creator")
        creator_label.set_halign(Gtk.Align.END)
        grid.attach(creator_label, 0, 2, 1, 1)
        self.__creator = Gtk.Entry()
        self.__creator.set_text(self.__main_window.project.creator)
        self.__creator.set_hexpand(True)
        self.__creator.set_halign(Gtk.Align.FILL)
        grid.attach(self.__creator, 1, 2, 2, 1)

        root_label = Gtk.Label("Project Root")
        root_label.set_halign(Gtk.Align.END)
        grid.attach(root_label, 0, 3, 1, 1)
        self.__root = Gtk.Entry()
        self.__root.set_text(self.__main_window.project.root)
        self.__root.set_hexpand(True)
        self.__root.set_halign(Gtk.Align.FILL)
        grid.attach(self.__root, 1, 3, 1, 1)
        root_button = Gtk.Button.new_with_label("...")
        root_button.connect('clicked', self.on_root_button)
        grid.attach(root_button, 2, 3, 1, 1)

        panic_fade_label = Gtk.Label("Panic Fade Time")
        panic_fade_label.set_halign(Gtk.Align.END)
        grid.attach(panic_fade_label, 0, 4, 1, 1)
        self.__panic_fade_time = TimePicker(initial_milliseconds=self.__main_window.project.panic_fade_time)
        self.__panic_fade_time.set_hexpand(True)
        self.__panic_fade_time.set_halign(Gtk.Align.FILL)
        grid.attach(self.__panic_fade_time, 1, 4, 1, 1)

        panic_delta_label = Gtk.Label("Panic Hard-Stop Delta")
        panic_delta_label.set_halign(Gtk.Align.END)
        panic_delta_label.set_tooltip_text(
            "Maximum time from clicking the panic button to count consecutive clicks as hard-stops"
        )
        grid.attach(panic_delta_label, 0, 5, 1, 1)
        self.__panic_delta = TimePicker(initial_milliseconds=self.__main_window.project.panic_hard_stop_time)
        self.__panic_delta.set_hexpand(True)
        self.__panic_delta.set_halign(Gtk.Align.FILL)
        grid.attach(self.__panic_delta, 1, 5, 1, 1)

        duration_difference_delta = Gtk.Label("Duration Difference Max Delta")
        duration_difference_delta.set_halign(Gtk.Align.END)
        duration_difference_delta.set_tooltip_text(
            "Maximum length difference between audio files to count them as different files"
        )
        grid.attach(duration_difference_delta, 0, 6, 1, 1)
        self.__duration_delta = TimePicker(
            initial_milliseconds=self.__main_window.project.max_duration_discovery_difference
        )
        self.__duration_delta.set_hexpand(True)
        self.__duration_delta.set_halign(Gtk.Align.FILL)
        grid.attach(self.__duration_delta, 1, 6, 1, 1)

        # TODO: Previous Revisions

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

    def on_root_button(self, button):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self.__main_window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            self.__root.set_text(dialog.get_filename())
        elif result == Gtk.ResponseType.CANCEL:
            logger.debug("CANCEL")
        dialog.destroy()

    def on_response(self, w, response):
        if response == Gtk.ResponseType.OK:
            self.__main_window.project.name = self.__name.get_text()
            self.__main_window.project.creator = self.__creator.get_text()
            self.__main_window.project.panic_fade_time = self.__panic_fade_time.get_total_milliseconds()
            self.__main_window.project.panic_hard_stop_time = self.__panic_delta.get_total_milliseconds()
            self.__main_window.project.max_duration_discovery_difference = self.__duration_delta.get_total_milliseconds()
            if self.__main_window.project.root != self.__root.get_text():
                self.__main_window.project.change_root(self.__root.get_text())
                self.__main_window.project.store()
            self.__main_window.update_title()


class SCCueDialog(Gtk.Dialog):
    def __init__(self, w, c, **properties):
        super().__init__("Cue Editor{0}".format(" - {0}".format(c.name) if c is not None else ""), w, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK),
                         **properties)

        self.__main_window = w
        self.__cue = c
        self.__editor = self.__cue.get_editor()

        grid = Gtk.Grid()
        grid.set_vexpand(True)
        grid.set_valign(Gtk.Align.FILL)

        id_label = Gtk.Label("Cue ID")
        id_label.set_halign(Gtk.Align.END)
        grid.attach(id_label, 0, 0, 1, 1)
        self.__id = Gtk.SpinButton.new_with_range(min=0.0, max=9999999999.0, step=0.1)
        self.__id.set_value(self.__cue.number)
        self.__id.set_hexpand(True)
        self.__id.set_halign(Gtk.Align.FILL)
        grid.attach(self.__id, 1, 0, 1, 1)

        name_label = Gtk.Label("Name")
        name_label.set_halign(Gtk.Align.END)
        grid.attach(name_label, 0, 1, 1, 1)
        self.__name = Gtk.Entry()
        self.__name.set_text(self.__cue.name)
        self.__name.set_hexpand(True)
        self.__name.set_halign(Gtk.Align.FILL)
        grid.attach(self.__name, 1, 1, 1, 1)

        desc_label = Gtk.Label("Description")
        desc_label.set_halign(Gtk.Align.END)
        grid.attach(desc_label, 0, 2, 1, 1)
        self.__description = Gtk.Entry()
        self.__description.set_text(self.__cue.description)
        self.__description.set_hexpand(True)
        self.__description.set_halign(Gtk.Align.FILL)
        grid.attach(self.__description, 1, 2, 1, 1)

        notes_label = Gtk.Label("Notes")
        notes_label.set_halign(Gtk.Align.END)
        grid.attach(notes_label, 0, 3, 1, 1)
        self.__text_buffer = Gtk.TextBuffer()
        self.__text_buffer.set_text(self.__cue.notes)
        self.__notes = Gtk.TextView.new_with_buffer(self.__text_buffer)
        self.__notes.set_wrap_mode(Gtk.WrapMode.WORD)
        self.__notes.set_hexpand(True)
        self.__notes.set_halign(Gtk.Align.FILL)
        self.__notes.set_vexpand(True)
        self.__notes.set_valign(Gtk.Align.FILL)
        wrapper = Gtk.ScrolledWindow()
        wrapper.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        wrapper.add(self.__notes)
        grid.attach(wrapper, 1, 3, 1, 1)

        prew_label = Gtk.Label("Pre-Wait Time")
        prew_label.set_halign(Gtk.Align.END)
        grid.attach(prew_label, 0, 4, 1, 1)
        self.__prewait = TimePicker(self.__cue.pre_wait)
        self.__prewait.set_hexpand(True)
        self.__prewait.set_halign(Gtk.Align.FILL)
        grid.attach(self.__prewait, 1, 4, 1, 1)

        postw_label = Gtk.Label("Post-Wait Time")
        postw_label.set_halign(Gtk.Align.END)
        grid.attach(postw_label, 0, 5, 1, 1)
        self.__postwait = TimePicker(self.__cue.post_wait)
        self.__postwait.set_hexpand(True)
        self.__postwait.set_halign(Gtk.Align.FILL)
        grid.attach(self.__postwait, 1, 5, 1, 1)

        if self.__editor:
            wrapper = Gtk.ScrolledWindow()
            wrapper.add(self.__editor)
            wrapper.set_hexpand(True)
            wrapper.set_halign(Gtk.Align.FILL)
            wrapper.set_vexpand(True)
            wrapper.set_valign(Gtk.Align.FILL)
            wrapper.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            grid.attach(wrapper, 0, 6, 2, 1)

        self.get_content_area().pack_start(grid, True, True, 0)
        self.set_modal(True)
        w, h = self.__main_window.get_size()
        g = Gdk.Geometry()
        g.min_width = int(float(w) * .7)
        g.max_width = int(float(w) * .7)
        g.min_height = int(float(h) * .7)
        g.max_height = int(float(h) * .9)
        self.set_geometry_hints(self, g, Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.MAX_SIZE)
        self.connect('response', self.on_response)
        self.show_all()

    def get_custom_editor(self):
        return self.__editor

    def get_cue(self):
        return self.__cue

    def on_response(self, w, response):
        if response == Gtk.ResponseType.OK:
            self.__cue.name = self.__name.get_text().strip()
            self.__cue.description = self.__description.get_text().strip()
            self.__cue.notes = self.__text_buffer.get_text(
                self.__text_buffer.get_start_iter(),
                self.__text_buffer.get_end_iter(),
                True
            )
            self.__cue.pre_wait = self.__prewait.get_total_milliseconds()
            self.__cue.post_wait = self.__postwait.get_total_milliseconds()
            self.__cue.number = self.__id.get_value()

            self.__cue.on_editor_closed(self.__editor, save=True)
        else:
            self.__cue.on_editor_closed(self.__editor, save=False)