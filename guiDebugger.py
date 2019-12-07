import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Main(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self, None)
        self.status = self.statusBar()
        self.tab_widget = DebugTabWidget(self)
        self.menubar = self.menuBar()
        self.toolbar = self.addToolBar('Debug actions')
        data = [{'1': 2, '3': 4}, {'5': 6, '7': 8}]
        self.stacktrace_widget = Stacktrace_Widget(data)
        self.stacktrace_widget.show()
        self.setCentralWidget(self.tab_widget)
        self.init_ui()

    def init_ui(self):
        open_action = QAction(QIcon("icons/open.png"), "Open file", self)
        open_action.setStatusTip("Open existing document")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open)

        self.toolbar.addAction(open_action)

        file = self.menubar.addMenu("File")
        file.addAction(open_action)

        self.setGeometry(100, 100, 1000, 1000)
        self.showMaximized()  # Doesn't work correctly without setGeometry()
        self.setWindowTitle("Python debugger")
        # self.setWindowIcon(QIcon("icons/feather.png"))
        self.show()

    def open(self):
        (filename, _) = QFileDialog.getOpenFileName(self, 'Open file')
        if not filename:
            return
        with open(filename, 'r') as file:
            data = ''
            for index, line in enumerate(file.readlines()):
                data += ' ' + str(index + 1) + '\t' + line
        new_tab = FileViewerWidget(data)
        self.tab_widget.add(new_tab, filename)
        self.attach_cursor_tracker(new_tab)

    def on_cursor_position_change(self):
        if len(self.tab_widget.tabs) > 0:
            line = self.tab_widget.tabs.currentWidget().textCursor(
            ).blockNumber()
            col = self.tab_widget.tabs.currentWidget().textCursor(
            ).columnNumber()
            linecol = ("Line: " + str(line + 1) + " | " + "Column: " + str(
                col + 1))
            self.status.showMessage(linecol)
            self.clear_highlights()
            self.highlight_line(line)
            if col == 0:
                self.get_breakpoint_dialog(line + 1)

    def attach_cursor_tracker(self, new_tab):
        new_tab.cursorPositionChanged.connect(self.on_cursor_position_change)

    def highlight_line(self, line):
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 0, 0))

        block = self.tab_widget.tabs.currentWidget().document(
        ).findBlockByLineNumber(line)
        block_pos = block.position()

        cursor = self.tab_widget.tabs.currentWidget().textCursor()
        cursor.setPosition(block_pos)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.setCharFormat(fmt)

    def clear_highlights(self):
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 255, 255))

        cursor = self.tab_widget.tabs.currentWidget().textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(fmt)

    def get_breakpoint_dialog(self, line_num):
        text, ok_pressed = \
            QInputDialog.getText(self, "Set breakpoint on {}".format(line_num),
                                 "Condition (empty means no condition)"
                                 , QLineEdit.Normal, "")
        if ok_pressed and text != '':
            print(text)


class Stacktrace_Widget(QWidget):
    def __init__(self, data):
        super(QWidget, self).__init__()
        self.tree = QTreeView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name', 'dbID'])
        self.tree.header().setDefaultSectionSize(180)
        self.tree.setModel(self.model)
        self.importData(data)

    def importData(self, data):
        self.model.setRowCount(0)
        root = self.model.invisibleRootItem()
        for index, stack_values in enumerate(data):
            parent = QStandardItem(str(index + 1))
            for key in stack_values.keys():
                parent.appendRow([QStandardItem(str(key)),
                                  QStandardItem(str(stack_values[key]))])
            root.appendRow(parent)


class FileViewerWidget(QTextEdit):
    def __init__(self, text):
        super(QTextEdit, self).__init__()
        self.setReadOnly(True)
        self.setText(text)


class DebugTabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.tabs_container = dict()

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def add(self, new_tab, filename):
        if filename not in self.tabs_container:
            self.tabs.addTab(new_tab, os.path.basename(filename))
            self.tabs_container[filename] = new_tab
        self.tabs.setCurrentWidget(self.tabs_container[filename])


def main():
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
