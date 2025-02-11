# -*- coding: utf-8 -*-

"""
Copyright (c) 2022 Colin Curtain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Author: Colin Curtain (ccbogel)
https://github.com/ccbogel/QualCoder
https://qualcoder.wordpress.com/
"""

import copy
import os
import sys
import logging
import traceback

from PyQt6 import QtCore, QtWidgets

from .GUI.ui_dialog_select_items import Ui_Dialog_selectitems
from .helpers import Message

path = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)


def exception_handler(exception_type, value, tb_obj):
    """ Global exception handler useful in GUIs.
    tb_obj: exception.__traceback__ """
    tb = '\n'.join(traceback.format_tb(tb_obj))
    text = 'Traceback (most recent call last):\n' + tb + '\n' + exception_type.__name__ + ': ' + str(value)
    print(text)
    logger.error(_("Uncaught exception: ") + text)
    QtWidgets.QMessageBox.critical(None, _('Uncaught Exception'), text)


class DialogSelectItems(QtWidgets.QDialog):
    """
    Requires a list of dictionaries. This list must have a dictionary item called 'name'
    Which is displayed to the user.
    Optionally have a dictionary item called 'group' (Used in View_graph)
    The group can be selected using the comboBox to limit items shown.
    The setupui method requires a title string for the dialog title and a selection mode:
    "single" or any other text which equates to many.

    User selects one or more names from the list depending on selection mode.
    getSelected method returns the selected dictionary object(s).

    Called by by ViewGraph, DialogCodeText, DialogCodeAV, DialogCodeImage
    """

    data = None
    groups = []
    data_refined = None
    model = None
    title = None

    def __init__(self, app_, data, title, selection_mode):
        """ present list of names to user for selection.

        params:
            data: list of dictionaries containing the key 'name'
            title: Dialog title, String
            selectionmode: 'single' or anything else for 'multiple', String
        """

        sys.excepthook = exception_handler
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_Dialog_selectitems()
        self.ui.setupUi(self)
        font = 'font: ' + str(app_.settings['fontsize']) + 'pt '
        font += '"' + app_.settings['font'] + '";'
        self.setStyleSheet(font)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint)
        self.setWindowTitle(title)
        self.data = data
        self.selection_mode = selection_mode
        # Check data exists
        if len(self.data) == 0:
            Message(app_, _('Dictionary is empty'), _("No data to select from"), "warning")
        # Check for 'name' key
        no_name_key = False

        self.groups = []
        for d in self.data:
            if not d['name']:
                no_name_key = True
            try:
                self.groups.append(d['group'])
            except KeyError:
                pass
        if no_name_key:
            text = _("This data does not contain names to select from")
            Message(app_, _('Dictionary has no "name" key'), text, "warning")
        if self.groups:
            self.groups = list(set(self.groups))
            self.groups.insert(0, _("All"))
            self.ui.comboBox.setEnabled(True)
            self.ui.comboBox.addItems(self.groups)

        if self.selection_mode == "single":
            self.ui.listView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        else:
            self.ui.listView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ui.listView.doubleClicked.connect(self.accept)
        self.model = None
        self.fill_list()
        self.ui.comboBox.currentIndexChanged.connect(self.fill_list)

    def fill_list(self):
        """ Show data items considering comboBox group selection. """

        self.data_refined = copy.copy(self.data)
        grouper = self.ui.comboBox.currentText()
        if not self.groups or grouper == "All":
            self.model = ListModel(self.data_refined)
            self.ui.listView.setModel(self.model)
            return

        self.data_refined = []
        for d in self.data:
            if d['group'] == grouper:
                self.data_refined.append(d)
        self.model = ListModel(self.data_refined)
        self.ui.listView.setModel(self.model)

    def get_selected(self):
        """ Get a selected dictionary  or a list of dictionaries depending on the
        selection mode.

        return: list if Dictionaries of {name, data} """

        if self.selection_mode == "single":
            current = self.ui.listView.currentIndex().row()
            if current == -1:
                return []
            return self.data_refined[int(current)]
        else:
            selected = []
            for item in self.ui.listView.selectedIndexes():
                selected.append(self.data_refined[item.row()])
            return selected


class ListModel(QtCore.QAbstractListModel):
    def __init__(self, data_list, parent=None):
        super(ListModel, self).__init__(parent)
        sys.excepthook = exception_handler
        self.list = data_list

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.list)

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:  # show just the name
            row_item = self.list[index.row()]
            return QtCore.QVariant(row_item['name'])
        elif role == QtCore.Qt.ItemDataRole.UserRole:  # return the whole python object
            row_item = self.list[index.row()]
            return row_item
        return QtCore.QVariant()
