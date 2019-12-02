import sys
import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Main(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self, None)
        self.status = self.statusBar()
        self.tab_widget = DebugTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        self.init_ui()

    def init_ui(self):
        open_action = QAction(QIcon("icons/open.png"), "Open file", self)
        open_action.setStatusTip("Open existing document")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open)

        self.showMaximized()
        self.setWindowTitle("Python debugger")
        # self.setWindowIcon(QIcon("icons/feather.png"))
        self.show()

        menubar = self.menuBar()
        file = menubar.addMenu("File")

        file.addAction(open_action)

    def open(self):
        (filename, _) = QFileDialog.getOpenFileName(self, 'Open file')
        with open(filename, 'r') as file:
            data = file.read()
        new_tab = FileViewerWidget(data)
        self.tab_widget.add(new_tab, filename)
        self.attach_cursor_tracker(new_tab)

    def cursor_position(self):
        if len(self.tab_widget.tabs) > 0:
            line = self.tab_widget.tabs.currentWidget().textCursor().blockNumber()
            col = self.tab_widget.tabs.currentWidget().textCursor().columnNumber()
            linecol = ("Line: " + str(line) + " | " + "Column: " + str(col))
            self.status.showMessage(linecol)
            self.clear_highlights()
            self.highlight_line(line)

    def attach_cursor_tracker(self, new_tab):
        new_tab.cursorPositionChanged.connect(self.cursor_position)

    def highlight_line(self, line):
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 0, 0))

        block = self.tab_widget.tabs.currentWidget().document().findBlockByLineNumber(line)
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
