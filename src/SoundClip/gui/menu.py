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

from gi.repository import Gtk, Gio
from SoundClip import __version__


class SCHeaderBar(Gtk.HeaderBar):
    """
    SoundClip's custom HeaderBar
    """

    def __init__(self, w, **properties):
        super().__init__(**properties)

        self.__main_window = w

        self.set_title("SoundClip " + __version__)
        self.set_subtitle("Unknown Project")
        self.set_show_close_button(True)

        self.__new_project_button = Gtk.Button.new_from_icon_name("document-new", Gtk.IconSize.SMALL_TOOLBAR)
        self.__new_project_button.set_tooltip_text("New Project")
        self.__new_project_button.connect("clicked", self.on_new_project)
        self.pack_start(self.__new_project_button)

        self.__save_as_button = Gtk.Button.new_from_icon_name("document-save-as", Gtk.IconSize.SMALL_TOOLBAR)
        self.__save_as_button.set_tooltip_text("Save Project As...")
        self.__save_as_button.connect("clicked", self.on_save_as)
        self.pack_start(self.__save_as_button)

        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.__add_cue_button = Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.SMALL_TOOLBAR)
        self.__add_cue_button.set_tooltip_text("Add Cue Here")
        self.__add_cue_button.connect("clicked", self.on_add_cue)
        self.pack_start(self.__add_cue_button)

        # When packing at the end, items must be specified rightmost first, working your way back towards the middle

        self.__settings_button = Gtk.Button.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.__settings_button.connect("clicked", self.on_settings)
        self.pack_end(self.__settings_button)

        self.__settings_menu = SCPopoverMenu()
        self.__settings_menu.set_relative_to(self.__settings_button)

        self.__lock_workspace_button = Gtk.ToggleButton()
        self.__lock_workspace_button.set_image(Gtk.Image.new_from_icon_name("system-lock-screen",
                                                                            Gtk.IconSize.SMALL_TOOLBAR))
        self.__lock_workspace_button.set_tooltip_text("Lock Workspace from Editing")
        self.__lock_workspace_button.connect("clicked", w.toggle_workspace_lock)
        self.pack_end(self.__lock_workspace_button)

        self.pack_end(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.__panic_button = Gtk.Button.new_from_icon_name("dialog-warning", Gtk.IconSize.SMALL_TOOLBAR) #TODO: Specify icon
        self.__panic_button.set_tooltip_text("PANIC: Stop all automations and cues")
        self.__panic_button.connect("clicked", self.on_panic)
        self.pack_end(self.__panic_button)

    def on_new_project(self, button):
        print("TODO: DO_NEW_PROJECT")

    def on_save_as(self, button):
        print("TODO: DO_SAVE_AS")

    def on_add_cue(self, button):
        print("TODO: DO_ADD_CUE")

    def on_panic(self, button):
        """
        Callback for the Panic Button. Stops all running cues and automation tasks
        """
        print("PANIC! Stopping all cues and automation")
        self.__main_window.send_stop_all()

    def on_settings(self, button):
        if self.__settings_menu.get_visible():
            self.__settings_menu.hide()
        else:
            self.__settings_menu.show_all()


class SCPopoverMenu(Gtk.Popover):
    """
    The menu displayed when the menu button is clicked
    """

    def __init__(self, **properties):
        super().__init__(**properties)

        self.__model = Gio.Menu()
        self.bind_model(self.__model)

        self.__about_action = Gio.SimpleAction.new('about-action', None)
        self.__about_action.connect("activate", lambda obj,btn: print("Foo!"))
        self.__model.append("About", "app.about-action")