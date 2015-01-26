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

import os
import logging
logger = logging.getLogger('SoundClip')

from gi.repository import Gtk, Gio

from SoundClip.cue import Cue, CueStack, AudioCue
from SoundClip.gui.dialog import SCCueDialog, SCProjectPropertiesDialog, SCAboutDialog, SCRenameCueListDialog
from SoundClip.project import Project


class SCHeaderBar(Gtk.HeaderBar):
    """
    SoundClip's custom HeaderBar
    """

    def __init__(self, w, **properties):
        super().__init__(**properties)

        self.__main_window = w
        self.__main_window.connect('lock-toggled', self.on_workspace_lock_toggle)

        self.set_show_close_button(True)

        self.__open_button = Gtk.Button.new_from_icon_name("document-open", Gtk.IconSize.SMALL_TOOLBAR)
        self.__open_button.set_tooltip_text("Open Project")
        self.__open_button.connect("clicked", self.on_open_project)
        self.pack_start(self.__open_button)

        self.__new_project_button = Gtk.Button.new_from_icon_name("document-new", Gtk.IconSize.SMALL_TOOLBAR)
        self.__new_project_button.set_tooltip_text("New Project")
        self.__new_project_button.connect("clicked", self.on_new_project)
        self.pack_start(self.__new_project_button)

        self.__save_as_button = Gtk.Button.new_from_icon_name("document-save-as", Gtk.IconSize.SMALL_TOOLBAR)
        self.__save_as_button.set_tooltip_text("Save Project As...")
        self.__save_as_button.connect("clicked", self.on_save_as)
        self.pack_start(self.__save_as_button)

        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.__add_cue_button = Gtk.MenuButton()
        self.__add_cue_button.add(Gtk.Image.new_from_icon_name("list-add", Gtk.IconSize.SMALL_TOOLBAR))
        self.__add_cue_model = SCAddCuemenu(self.__main_window)
        self.__add_cue_button.set_menu_model(self.__add_cue_model)
        self.__add_cue_button.insert_action_group('cue', self.__add_cue_model.get_action_group())
        self.__add_cue_button.set_tooltip_text("Add...")
        self.pack_start(self.__add_cue_button)

        # When packing at the end, items must be specified rightmost first, working your way back towards the middle
        self.__settings_button = Gtk.MenuButton()
        self.__settings_button.add(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.SMALL_TOOLBAR))
        self.__settings_model = SCSettingsMenuModel(self.__main_window)
        self.__settings_button.set_menu_model(self.__settings_model)
        self.__settings_button.insert_action_group('hb', self.__settings_model.get_action_group())
        self.__settings_button.set_tooltip_text("Properties")
        self.pack_end(self.__settings_button)

        self.__lock_workspace_button = Gtk.ToggleButton()
        self.__lock_workspace_button.set_image(Gtk.Image.new_from_icon_name("system-lock-screen",
                                                                            Gtk.IconSize.SMALL_TOOLBAR))
        self.__lock_workspace_button.set_tooltip_text("Lock Workspace from Editing")
        self.__lock_workspace_button.connect("clicked", w.toggle_workspace_lock)
        self.pack_end(self.__lock_workspace_button)

        self.pack_end(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.__panic_button = Gtk.Button.new_from_icon_name("dialog-warning",
                                                            Gtk.IconSize.SMALL_TOOLBAR)  # TODO: Specify icon
        self.__panic_button.set_tooltip_text("PANIC: Stop all automations and cues")
        self.__panic_button.connect("clicked", self.on_panic)
        self.pack_end(self.__panic_button)

    def on_workspace_lock_toggle(self, obj, lock):
        self.__add_cue_button.set_sensitive(not lock)
        self.__open_button.set_sensitive(not lock)
        self.__new_project_button.set_sensitive(not lock)

    def on_open_project(self, button):
        # TODO: Save existing project if needed
        dialog = Gtk.FileChooserDialog("Please choose a folder", self.__main_window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            proj = dialog.get_filename()
            logger.debug("Opening from {0}".format(proj))
            p = Project.load(proj)
            if p:
                self.__main_window.change_project(p)
        elif result == Gtk.ResponseType.CANCEL:
            logger.debug("CANCEL")
        dialog.destroy()

    def on_new_project(self, button):
        # TODO: Save existing project if needed
        dialog = Gtk.FileChooserDialog("Please choose a folder", self.__main_window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            proj = dialog.get_filename()
            if os.path.isdir(os.path.join(proj, ".soundclip")):
                logger.error("Project exists!")
                d = Gtk.MessageDialog(self.__main_window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                      "Error: Project Exists")
                d.format_secondary_text("You cannot create a new project in the same directory as an existing one.")
                d.run()
                d.destroy()
            else:
                logger.info("Saving new project to {0}".format(proj))
                p = Project()
                p.root = proj
                self.__main_window.change_project(p)
                # TODO: Project Properties window?
        elif result == Gtk.ResponseType.CANCEL:
            logger.debug("CANCEL")
        dialog.destroy()

    def on_save_as(self, button):
        root = self.__main_window.project.root

        if not root:
            dialog = Gtk.FileChooserDialog("Please choose a folder", self.__main_window,
                                           Gtk.FileChooserAction.SELECT_FOLDER,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK))
            dialog.set_default_size(800, 400)

            result = dialog.run()
            if result == Gtk.ResponseType.OK:
                root = dialog.get_filename()
                logger.info("Saving to {0}".format(root))
                self.__main_window.project.root = root
            elif result == Gtk.ResponseType.CANCEL:
                logger.debug("CANCEL")

            dialog.destroy()

        self.__main_window.project.store()
        self.__main_window.update_title()

    def on_panic(self, button):
        """
        Callback for the Panic Button. Stops all running cues and automation tasks
        """
        p = self.__main_window.project
        ft = p.panic_fade_time
        logger.warning("PANIC! Stopping all cues and automation over {0} ms".format(
            self.__main_window.project.panic_fade_time
        ))
        self.__main_window.send_stop_all(fade=1000)


class SCSettingsMenuModel(Gio.Menu):
    """
    The menu displayed when the menu button is clicked
    """

    def __init__(self, w, **properties):
        super().__init__(**properties)

        self.__main_window = w

        self.__action_group = Gio.SimpleActionGroup()

        rename_action = Gio.SimpleAction.new("rename", None)
        rename_action.connect("activate", self.on_rename)
        self.append("Rename CueList", "hb.rename")
        self.__action_group.insert(rename_action)

        properties_action = Gio.SimpleAction.new("properties", None)
        properties_action.connect("activate", self.on_properties)
        self.append("Project Properties", "hb.properties")
        self.__action_group.insert(properties_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.append("About", "hb.about")
        self.__action_group.insert(about_action)

    def on_rename(self, model, user_data):
        d = SCRenameCueListDialog(self.__main_window, self.__main_window.get_current_cue_stack().name)
        result = d.run()
        if result == Gtk.ResponseType.OK:
            self.__main_window.get_current_cue_stack().rename(d.get_name())
        d.destroy()

    def on_about(self, model, user_data):
        d = SCAboutDialog(self.__main_window)
        d.run()
        d.destroy()

    def on_properties(self, model, user_data):
        d = SCProjectPropertiesDialog(self.__main_window)
        d.run()
        d.destroy()

    def get_action_group(self):
        return self.__action_group


class SCAddCuemenu(Gio.Menu):
    def __init__(self, w, **properties):
        super().__init__(**properties)

        self.__main_window = w
        self.__action_group = Gio.SimpleActionGroup()
        
        blank_cue = Gio.SimpleAction.new("blank", None)
        blank_cue.connect('activate', self.on_blank_cue)
        self.append("Blank Cue", "cue.blank")
        self.__action_group.insert(blank_cue)
        
        audio_cue = Gio.SimpleAction.new("audio", None)
        audio_cue.connect('activate', self.on_audio_cue)
        self.append("Audio Cue", "cue.audio")
        self.__action_group.insert(audio_cue)
        
        cue_list = Gio.SimpleAction.new("list", None)
        cue_list.connect('activate', self.on_cue_list)
        self.append("Cue List", "cue.list")
        self.__action_group.insert(cue_list)

    def on_blank_cue(self, model, user_data):
        current = self.__main_window.get_selected_cue()
        logger.debug("Current cue is {0}".format(current.name if current else "None"))
        c = Cue(self.__main_window.project)
        c.number = current.number + 1 if current else 1

        self.display_add_dialog_for(current, c)
    
    def on_audio_cue(self, model, user_data):
        current = self.__main_window.get_selected_cue()
        logger.debug("Current cue is {0}".format(current.name if current else "None"))
        c = AudioCue(self.__main_window.project)
        c.number = current.number + 1 if current else 1

        self.display_add_dialog_for(current, c)

    def display_add_dialog_for(self, current, c):
        dialog = SCCueDialog(self.__main_window, c)
        result = dialog.run()
        dialog.destroy()

        if result == Gtk.ResponseType.OK:
            self.__main_window.add_cue_relative_to(current, c)
        else:
            pass
    
    def on_cue_list(self, model, user_data):
        cl = CueStack(name="Untitled Cue List", project=self.__main_window.project)
        d = SCRenameCueListDialog(self.__main_window, cl.name)
        result = d.run()
        if result == Gtk.ResponseType.OK:
            cl.rename(d.get_name())
            logger.debug("Adding CueList {0}".format(cl.name))
            self.__main_window.project.add_cuelist(cl)
        d.destroy()

    def get_action_group(self):
        return self.__action_group