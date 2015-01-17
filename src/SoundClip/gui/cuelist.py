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

from gi.repository import Gtk, Gdk, cairo

from SoundClip import util
from SoundClip.cue import PlaybackState, CueStackChangeType
from SoundClip.gui.dialog import SCCueDialog


class SCCueListModel(Gtk.TreeStore):
    """
    The model for the cue list
    """

    column_types = (str, str, str, str, float, str, float, str, float, str)

    def __init__(self, cue_list):
        super().__init__()
        self.__cue_list = cue_list
        self.__cue_list.connect('changed', self.on_cuelist_changed)

    def on_cuelist_changed(self, obj, index, csct):
        if csct == CueStackChangeType.INSERT:
            self.row_inserted(Gtk.TreePath.new_from_indices((index,)), Gtk.TreeIter())
        elif csct == CueStackChangeType.UPDATE:
            self.row_changed(Gtk.TreePath.new_from_indices((index,)), Gtk.TreeIter())
        elif csct == CueStackChangeType.DELETE:
            self.row_deleted(Gtk.TreePath.new_from_indices((index,)))

    def get_cue_at(self, path):
        return self.__cue_list[path.get_indices()[0]]

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
            4: 0 if self.__cue_list[itr.user_data].pre_wait <= 0 else self.__cue_list[itr.user_data].elapsed_prewait /
                                                                      self.__cue_list[itr.user_data].pre_wait,
            5: self.__elapsed_pre(self.__cue_list[itr.user_data]),
            6: 0 if self.__cue_list[itr.user_data].duration <= 0 else self.__cue_list[itr.user_data].elapsed /
                                                                      self.__cue_list[itr.user_data].duration,
            7: self.__elapsed(self.__cue_list[itr.user_data]),
            8: 0 if self.__cue_list[itr.user_data].post_wait <= 0 else self.__cue_list[itr.user_data].elapsed_postwait /
                                                                      self.__cue_list[itr.user_data].post_wait,
            9: self.__elapsed_post(self.__cue_list[itr.user_data]),
        }.get(column, None)

    def do_set_value(self, itr, column):
        """
        Model should be read-only. May be revisited in the future
        """
        pass

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


class SCCueListMenu(Gtk.Popover):
    """
    The context menu displayed when a cue is right-clicked
    """

    def __init__(self, view, **properties):
        super().__init__(**properties)
        self.__tree_view = view
        self.set_relative_to(self.__tree_view)
        self.__focused_cue = None

        self.__box = Gtk.Box()

    def popover_cue(self, cue, x, y):
        r = cairo.RectangleInt()
        r.x = x
        r.y = y + 25
        r.width = 0
        r.height = 0
        self.set_pointing_to(r)
        self.set_position(Gtk.PositionType.BOTTOM)
        self.__focused_cue = cue

        self.remove(self.__box)
        self.__box = Gtk.Box()
        if self.__focused_cue.state is PlaybackState.PAUSED or self.__focused_cue.state is PlaybackState.PLAYING:
            pass
        else:
            pass

        logger.debug("Popping over [{0:g}]{1}".format(self.__focused_cue.number, self.__focused_cue.name))
        self.show_all()

    def on_edit(self):
        logger.debug("TODO: Edit cue [{0:g}]{1}".format(self.__focused_cue.number, self.__focused_cue.name))


class SCCueList(Gtk.ScrolledWindow):
    """
    A graphical representation of a cue list

    TODO: How do I get the bloody columns to size properly?
    """

    def __init__(self, w, cue_list, **properties):
        super().__init__(**properties)
        self.__main_window = w
        self.__cue_list = cue_list
        self.__tree_view = Gtk.TreeView()
        self.__popover = SCCueListMenu(self.__tree_view)

        self.__title_widget = Gtk.Label(cue_list.name)
        self.__cue_list.connect('renamed', self.on_rename)

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
        self.__tree_view.connect('key-release-event', self.on_key)
        self.__tree_view.connect('button-press-event', self.on_click)

        self.add(self.__tree_view)

    def get_selected(self):
        if len(self.__cue_list) <= 0:
            return None
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        if not pathlist:
            return None
        logger.debug("Getting Cue")
        return self.__model.get_cue_at(pathlist[0])

    def get_title_widget(self):
        return self.__title_widget

    def select_previous(self):
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        self.__tree_view.set_cursor(Gtk.TreePath(pathlist[0].get_indices()[0]-1), None, False)

    def select_next(self):
        (model, pathlist) = self.__tree_view.get_selection().get_selected_rows()
        self.__tree_view.set_cursor(Gtk.TreePath(pathlist[0].get_indices()[0]+1), None, False)

    def on_rename(self, obj, name):
        self.__title_widget.set_text(name)

    def on_click(self, view, event):
        if self.__main_window.locked:
            return
        x, y = int(event.x), int(event.y)
        path = self.__tree_view.get_path_at_pos(x, y)
        cue = self.__cue_list[path[0].get_indices()[0]]
        if event.button is Gdk.BUTTON_SECONDARY:
            self.__popover.popover_cue(cue, x, y)
        elif event.button is Gdk.BUTTON_PRIMARY and event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
            dialog = SCCueDialog(self.__main_window, cue)
            dialog.run()
            dialog.destroy()

    def on_key(self, view, event):
        if event.keyval is Gdk.KEY_space:
            c = self.get_selected()
            logger.debug("Type of selected cue is {0}".format(str(type(c))))
            logger.debug(c.go)
            c.go()
            self.select_next()
            return False
        return True

    def get_stack(self):
        return self.__cue_list