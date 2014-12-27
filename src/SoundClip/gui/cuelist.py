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
from gi.repository import GObject
from SoundClip.cue import AutoFollowType


class SCCueListModel(Gtk.TreeStore):
    """
    """

    column_types = (str, str, str, float, GObject.TYPE_LONG, GObject.TYPE_LONG, GObject.TYPE_OBJECT,
                    GObject.TYPE_OBJECT)

    def __init__(self, cue_list):
        super().__init__()
        self.__cue_list = cue_list

    def do_get_flags(self):
        return Gtk.TreeModelFlags.ITERS_PERSIST

    def do_get_n_columns(self):
        return len(self.column_types)

    def do_get_column_type(self, n):
        return self.column_types[n]

    def do_get_iter(self, path):
        index = path.get_indices()[0]
        if index < 0 or index >= len(self.__cue_list):
            return False, None

        itr = Gtk.TreeIter()
        itr.user_data = index
        return True, itr

    def do_get_path(self, itr):
        return Gtk.TreePath([itr.user_data])

    def do_get_value(self, itr, column):
        # TODO: What to do here?
        return {
            0: self.__cue_list[itr.user_data].name,
            1: self.__cue_list[itr.user_data].description,
            2: self.__cue_list[itr.user_data].notes,
            3: self.__cue_list[itr.user_data].number,
            4: self.__cue_list[itr.user_data].pre_wait,
            5: self.__cue_list[itr.user_data].post_wait,
            6: self.__cue_list[itr.user_data].autofollow_target,
            7: self.__cue_list[itr.user_data].autofollow_type,
        }.get(column, None)

    def do_iter_next(self, itr):
        next_index = itr.user_data + 1
        if next_index >= len(self.__cue_list):
            return False

        itr.user_data = next_index
        return True

    def do_iter_previous(self, itr):
        prev_index = itr.user_data - 1
        if prev_index < 0:
            return False

        itr.user_data = prev_index
        return True

    def do_iter_children(self, parent):
        if parent is None:
            itr = Gtk.TreeIter()
            itr.user_data = 0
            return True, itr
        return False, None

    def do_iter_has_child(self, itr):
        return itr is None

    def do_iter_n_children(self, itr):
        return len(self.__cue_list) if itr is None else 0

    def do_iter_nth_child(self, parent, n):
        if parent is not None or n >= len(self.__cue_list):
            return False, None
        else:
            itr = Gtk.TreeIter()
            itr.user_data = n
            return True, itr

    def do_iter_parent(self, child):
        return False, None


class SCCueList(Gtk.TreeView):
    """
    A graphical representation of a cue list
    """

    def __init__(self, cue_list, **properties):
        super().__init__(**properties)
        self.__cue_list = cue_list

        self.__model = SCCueListModel(self.__cue_list)
        self.set_model(self.__model)

        self.__number_col_renderer = Gtk.CellRendererText()
        self.__number_col = Gtk.TreeViewColumn(title="#", cell_renderer=self.__number_col_renderer, text=4)
        self.append_column(self.__number_col)

        self.__name_col_renderer = Gtk.CellRendererText()
        self.__name_col = Gtk.TreeViewColumn(title="Name", cell_renderer=self.__name_col_renderer, text=0)
        self.append_column(self.__name_col)

        self.__desc_col_renderer = Gtk.CellRendererText()
        self.__desc_col = Gtk.TreeViewColumn(title="Description", cell_renderer=self.__desc_col_renderer, text=1)
        self.append_column(self.__desc_col)
        
        self.__prew_col_renderer = Gtk.CellRendererProgress()
        self.__prew_col = Gtk.TreeViewColumn(title="Pre-Wait", cell_renderer=self.__prew_col_renderer)
        self.append_column(self.__prew_col)
        
        self.__duration_col_renderer = Gtk.CellRendererProgress()
        self.__duration_col = Gtk.TreeViewColumn(title="Duration", cell_renderer=self.__duration_col_renderer)
        self.append_column(self.__duration_col)
        
        self.__postw_col_renderer = Gtk.CellRendererProgress()
        self.__postw_col = Gtk.TreeViewColumn(title="Post-Wait", cell_renderer=self.__postw_col_renderer)
        self.append_column(self.__postw_col)