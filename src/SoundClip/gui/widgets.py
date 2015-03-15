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

from SoundClip import util


class TimePicker(Gtk.Box):
    def __init__(self, initial_milliseconds=0, **properties):
        super().__init__(**properties)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        mm, ss, ms = util.timepart(initial_milliseconds)

        self.__minute_adjustment = Gtk.Adjustment(0, 0, step_increment=1, page_increment=1, page_size=1)
        self.__minute_button = Gtk.SpinButton()
        self.__minute_button.set_adjustment(self.__minute_adjustment)
        self.__minute_button.set_value(mm)
        self.pack_start(self.__minute_button, True, True, 0)
        self.pack_start(Gtk.Label("minutes, "), False, False, 5)

        self.__second_adjustment = Gtk.Adjustment(0, 0, 59, 1, 1, 1)
        self.__second_button = Gtk.SpinButton()
        self.__second_button.set_adjustment(self.__second_adjustment)
        self.__second_button.set_value(ss)
        self.pack_start(self.__second_button, True, True, 0)
        self.pack_start(Gtk.Label("seconds, "), False, False, 5)

        self.__millisecond_adjustment = Gtk.Adjustment(0, 0, 999, 1, 1, 1)
        self.__millisecond_button = Gtk.SpinButton()
        self.__millisecond_button.set_adjustment(self.__millisecond_adjustment)
        self.__millisecond_button.set_value(ms)
        self.pack_start(self.__millisecond_button, True, True, 0)
        self.pack_start(Gtk.Label("milliseconds"), False, False, 5)

    def get_minutes(self):
        return self.__minute_button.get_value_as_int()

    def get_seconds(self):
        return self.__second_button.get_value_as_int()

    def get_milliseconds(self):
        return self.__millisecond_button.get_value_as_int()

    def get_total_milliseconds(self):
        return (self.get_minutes() * 60 + self.get_seconds()) * 1000 + self.get_milliseconds()


class TransportControls(Gtk.Grid):
    def __init__(self, w):
        super().__init__()

        self.__main_window = w

        self.set_hexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_vexpand(False)
        self.set_valign(Gtk.Align.FILL)

        self.__text_buffer = Gtk.TextBuffer()
        self.__text_view = Gtk.TextView.new_with_buffer(self.__text_buffer)
        self.__text_view.set_editable(False)
        self.__text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.__text_view.set_hexpand(True)
        self.__text_view.set_halign(Gtk.Align.FILL)
        self.__text_view.set_vexpand(True)
        self.__text_view.set_valign(Gtk.Align.FILL)
        wrapper = Gtk.ScrolledWindow()
        wrapper.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        wrapper.add(self.__text_view)
        self.attach(wrapper, 0, 0, 1, 2)

        w, h = self.__main_window.get_size()
        button_size = Gdk.Geometry()
        button_size.min_width = button_size.max_width = int((float(w) * .5) / 3)
        button_size.min_height = button_size.max_height = int(50)

        self.__seek_back_small = Gtk.Button.new_from_icon_name("media-seek-backward", Gtk.IconSize.LARGE_TOOLBAR)
        self.__seek_back_small.set_tooltip_text("Rewind 15s")
        self.__seek_back_small.connect('clicked', self.on_seek)
        self.__seek_back_small.set_hexpand(False)
        self.__seek_back_small.set_halign(Gtk.Align.FILL)
        self.__seek_back_small.set_vexpand(False)
        self.__seek_back_small.set_valign(Gtk.Align.FILL)
        self.attach(self.__seek_back_small, 1, 0, 1, 1)
        
        self.__seek_back_large = Gtk.Button.new_from_icon_name("media-skip-backward", Gtk.IconSize.LARGE_TOOLBAR)
        self.__seek_back_large.set_tooltip_text("Rewind 30s")
        self.__seek_back_large.connect('clicked', self.on_seek)
        self.__seek_back_large.set_hexpand(False)
        self.__seek_back_large.set_halign(Gtk.Align.FILL)
        self.__seek_back_large.set_vexpand(False)
        self.__seek_back_large.set_valign(Gtk.Align.FILL)
        self.attach(self.__seek_back_large, 1, 1, 1, 1)
        
        self.__seek_forward_small = Gtk.Button.new_from_icon_name("media-seek-forward", Gtk.IconSize.LARGE_TOOLBAR)
        self.__seek_forward_small.set_tooltip_text("Fast-Forward 15s")
        self.__seek_forward_small.connect('clicked', self.on_seek)
        self.__seek_forward_small.set_hexpand(False)
        self.__seek_forward_small.set_halign(Gtk.Align.FILL)
        self.__seek_forward_small.set_vexpand(False)
        self.__seek_forward_small.set_valign(Gtk.Align.FILL)
        self.attach(self.__seek_forward_small, 2, 0, 1, 1)
        
        self.__seek_forward_large = Gtk.Button.new_from_icon_name("media-skip-forward", Gtk.IconSize.LARGE_TOOLBAR)
        self.__seek_forward_large.set_tooltip_text("Fast-Forward 30s")
        self.__seek_forward_large.connect('clicked', self.on_seek)
        self.__seek_forward_large.set_hexpand(False)
        self.__seek_forward_large.set_halign(Gtk.Align.FILL)
        self.__seek_forward_large.set_vexpand(False)
        self.__seek_forward_large.set_valign(Gtk.Align.FILL)
        self.attach(self.__seek_forward_large, 2, 1, 1, 1)
        
        self.__resume_all = Gtk.Button.new_from_icon_name("media-playback-start", Gtk.IconSize.LARGE_TOOLBAR)
        self.__resume_all.set_tooltip_text("Resume All")
        self.__resume_all.connect('clicked', self.on_playback_state)
        self.__resume_all.set_hexpand(False)
        self.__resume_all.set_halign(Gtk.Align.FILL)
        self.__resume_all.set_vexpand(False)
        self.__resume_all.set_valign(Gtk.Align.FILL)
        self.attach(self.__resume_all, 3, 0, 1, 1)

        self.__pause_all = Gtk.Button.new_from_icon_name("media-playback-pause", Gtk.IconSize.LARGE_TOOLBAR)
        self.__pause_all.set_tooltip_text("Pause All")
        self.__pause_all.connect('clicked', self.on_playback_state)
        self.__pause_all.set_hexpand(False)
        self.__pause_all.set_halign(Gtk.Align.FILL)
        self.__pause_all.set_vexpand(False)
        self.__pause_all.set_valign(Gtk.Align.FILL)
        self.attach(self.__pause_all, 3, 1, 1, 1)

    def set_notes(self, text):
        self.__text_buffer.set_text(text)

    def on_seek(self, button):
        if button is self.__seek_back_large:
            self.__main_window.try_seek_all(-30000)
        elif button is self.__seek_back_small:
            self.__main_window.try_seek_all(-15000)
        elif button is self.__seek_forward_small:
            self.__main_window.try_seek_all(15000)
        elif button is self.__seek_forward_large:
            self.__main_window.try_seek_all(30000)
    
    def on_playback_state(self, button):
        if button is self.__pause_all:
            self.__main_window.send_pause_all()
        elif button is self.__resume_all:
            self.__main_window.send_resume_all()