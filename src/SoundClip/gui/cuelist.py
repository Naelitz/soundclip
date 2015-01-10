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
from SoundClip.cue import PlaybackState


class SCCueListModel(Gtk.TreeStore):
    """
    """

    column_types = (str, str, str, str, float, str, float, str, float, str)

    def __init__(self, cue_list):
        super().__init__()
        self.__cue_list = cue_list

    def get_cue_at(self, itr):
        return self.__cue_list[itr.user_data]

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

    @staticmethod
    def __elapsed_pre(cue):
        return util.timefmt(cue.elapsed_prewait if cue.state is not PlaybackState.STOPPED else cue.pre_wait)

    @staticmethod
    def __elapsed(cue):
        return util.timefmt(cue.elapsed if cue.state is not PlaybackState.STOPPED else cue.duration)

    @staticmethod
    def __elapsed_post(cue):
        return util.timefmt(cue.elapsed_postwait if cue.state is not PlaybackState.STOPPED else cue.post_wait)

    def do_get_value(self, itr, column):
        return {
            0: self.__cue_list[itr.user_data].name,
            1: self.__cue_list[itr.user_data].description,
            2: self.__cue_list[itr.user_data].notes,
            3: '{0:g}'.format(self.__cue_list[itr.user_data].number),
            4: 0 if self.__cue_list[itr.user_data].pre_wait is 0 else self.__cue_list[itr.user_data].elapsed_prewait /
                                                                      self.__cue_list[itr.user_data].pre_wait,
            5: self.__elapsed_pre(self.__cue_list[itr.user_data]),
            6: 0 if self.__cue_list[itr.user_data].duration is 0 else self.__cue_list[itr.user_data].elapsed /
                                                                      self.__cue_list[itr.user_data].duration,
            7: self.__elapsed(self.__cue_list[itr.user_data]),
            8: 0 if self.__cue_list[itr.user_data].post_wait is 0 else self.__cue_list[itr.user_data].elapsed_postwait /
                                                                      self.__cue_list[itr.user_data].post_wait,
            9: self.__elapsed_post(self.__cue_list[itr.user_data]),
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


class SCCueList(Gtk.ScrolledWindow):
    """
    A graphical representation of a cue list

    TODO: How do I get the bloody columns to size properly?
    """

    def __init__(self, cue_list, **properties):
        super().__init__(**properties)
        self.__cue_list = cue_list
        self.__tree_view = Gtk.TreeView()

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.__model = SCCueListModel(self.__cue_list)
        self.__tree_view.set_model(self.__model)

        self.__number_col_renderer = Gtk.CellRendererText()
        self.__number_col = Gtk.TreeViewColumn(title="#", cell_renderer=self.__number_col_renderer, text=3)
        self.__number_col.set_fixed_width(64)
        self.__number_col.set_alignment(0.5)
        self.__tree_view.append_column(self.__number_col)

        self.__name_col_renderer = Gtk.CellRendererText()
        self.__name_col = Gtk.TreeViewColumn(title="Name", cell_renderer=self.__name_col_renderer, text=0)
        self.__name_col.set_alignment(0.5)
        self.__name_col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.__name_col.set_expand(False)
        self.__tree_view.append_column(self.__name_col)

        self.__desc_col_renderer = Gtk.CellRendererText()
        self.__desc_col = Gtk.TreeViewColumn(title="Description", cell_renderer=self.__desc_col_renderer, text=1)
        self.__desc_col.set_alignment(0.5)
        self.__desc_col.set_expand(True)
        self.__tree_view.append_column(self.__desc_col)

        self.__prew_col_renderer = Gtk.CellRendererProgress()
        self.__prew_col = Gtk.TreeViewColumn(title="Pre Wait", cell_renderer=self.__prew_col_renderer, value=4, text=5)
        self.__prew_col.set_alignment(0.5)
        self.__prew_col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.__prew_col.set_min_width(128)
        self.__prew_col.set_expand(False)
        self.__tree_view.append_column(self.__prew_col)

        self.__duration_col_renderer = Gtk.CellRendererProgress()
        self.__duration_col = Gtk.TreeViewColumn(title="Action", cell_renderer=self.__duration_col_renderer, value=6,
                                                 text=7)
        self.__duration_col.set_alignment(0.5)
        self.__duration_col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.__duration_col.set_min_width(128)
        self.__duration_col.set_expand(False)
        self.__tree_view.append_column(self.__duration_col)

        self.__postw_col_renderer = Gtk.CellRendererProgress()
        self.__postw_col = Gtk.TreeViewColumn(title="Post Wait", cell_renderer=self.__postw_col_renderer, value=8,
                                              text=9)
        self.__postw_col.set_alignment(0.5)
        self.__postw_col.set_min_width(128)
        self.__postw_col.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.__postw_col.set_expand(False)
        self.__tree_view.append_column(self.__postw_col)

        self.__tree_view.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        self.__tree_view.connect('key-press-event', self.on_key)

        self.add(self.__tree_view)

    def get_selected(self):
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        return self.__model.get_cue_at(tree_iter)

    def select_previous(self):
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        self.__tree_view.set_cursor(Gtk.TreePath(pathlist[0].get_indices()[0]-1), None, False)

    def select_next(self):
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        self.__tree_view.set_cursor(Gtk.TreePath(pathlist[0].get_indices()[0]+1), None, False)

    def on_key(self, view, event):
        if event.keyval is Gdk.KEY_space:
            self.get_selected().go()
            self.select_next()
        else:
            return False
        return True