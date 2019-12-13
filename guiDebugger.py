from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QTextCursor
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, \
    QApplication, QFileDialog, QMessageBox, QWidget, \
    QVBoxLayout, QTreeView, QInputDialog, QTextEdit, QHBoxLayout
from core.editor import Editor
import core.debugger as debugger
from PyQt5.QtCore import QCoreApplication
import sys
from io import StringIO
import os


class Main(QMainWindow):
    """Class Main, contains following functions:
    UI Initialization, Menu Initialization"""

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)
        self.main_widget.setLayout(self.layout)
        self.tab = Tab()
        self.tab.setStyleSheet("""
        QTabWidget::pane {background: #272727;}
        QTabWidget::tab-bar:top {top: 1px;}
        QTabWidget::tab-bar:bottom {bottom: 1px;}
        QTabWidget::tab-bar:left {right: 1px;}
        QTabWidget::tab-bar:right {left: 1px;}
        QTabBar{background-color: #1b1b1b; qproperty-drawBase:0;  }

        QTabBar::tab {border: 1px #1b1b1b;}
        QTabBar::tab:selected {background: #2b2b2b;color: #bbbbbb;}
        QTabBar::tab:!selected {background: #3c3e3f;color: #bbbbbb;}
        QTabBar::tab:bottom:!selected {margin-bottom: 3px;}
        QTabBar::tab:top, QTabBar::tab:bottom {
            min-width: 8ex;
            margin-right: -1px;
            padding: 5px 10px 5px 10px;}
        QTabBar::close-button {
            image: url(icons/close_hover.svg)
        }
        QTabBar::close-button:hover {
            image: url(icons/close.svg)
        }
        """)
        self.set_window_ui()
        self.set_menu()
        self.toolbar = self.addToolBar('Debug actions')
        data = [{'1': 2, '3': 4}, {'5': 6, '7': 8}]
        self.stacktrace_widget = StacktraceWidget(data)
        self.layout.addWidget(self.tab)
        self.sub_layout = QHBoxLayout()
        self.sub_layout.addWidget(self.stacktrace_widget)
        self.output_widget = QDbgConsole()
        self.sub_layout.addWidget(self.output_widget)
        self.layout.addLayout(self.sub_layout)
        self.setCentralWidget(self.main_widget)

    def set_window_ui(self):
        """UI Initialization"""
        self.setWindowTitle("Veredit")
        self.resize(1000, 500)
        self.setWindowIcon(QIcon('icons/veredit.ico'))
        self.showMaximized()

    def set_menu(self):
        """Menu Initialization"""
        menu = self.menuBar()

        # FILE MENU
        file_menu = menu.addMenu('&File')
        file_menu.addAction(QAction(QIcon('icons/open.svg'), '&Open FIle', self,
                                    shortcut='Ctrl+O',
                                    triggered=self._open_file))
        file_menu.addAction(
            QAction(QIcon('icons/power.svg'), '&Quit', self, shortcut='Ctrl+Q',
                    triggered=self._quit))

        # HELP MENU
        help_menu = menu.addMenu('&Help')
        help_menu.addAction(
            QAction(QIcon('icons/info.svg'), '&Info', self, shortcut='Ctrl+I',
                    triggered=self._about))

    def _open_file(self):
        """Open file and set it in a new tab or in current if tab is empty"""
        file = QFileDialog.getOpenFileName(self, 'Open file', ".")[0]
        if file:
            if file not in self.tab.tab_container:
                file_name = os.path.basename(file)
                editor = Editor()
                with open(file, 'r') as text:
                    self.tab.addTab(editor, file_name)
                    editor.setText(text.read())
                self.tab.tab_container[file] = editor
            self.tab.setCurrentWidget(self.tab.tab_container[file])

    def _about(self):
        QMessageBox.about(self, 'About Python Debugger', 'Some information')

    def _quit(self):
        QCoreApplication.quit()

    


class Tab(QTabWidget):
    count = 0

    def __init__(self):
        super(Tab, self).__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        self.tab_container = dict()

    def addTab(self, widget, filename):
        super(Tab, self).addTab(widget, filename)

    def removeTab(self, index):
        tab_to_remove = super(Tab, self).widget(index)
        self.tab_container = {filename: tab for filename, tab
                              in self.tab_container.items()
                              if tab != tab_to_remove}
        super(Tab, self).removeTab(index)


class StacktraceWidget(QWidget):
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


class InputGUI:
    def __init__(self, parentWidget):
        self.parentWidget = parentWidget

    def readline(self):
        text, ok = QInputDialog.getText(self.parentWidget, 'Introduce value',
                                        'Value:')
        if ok:
            return str(text)
        else:
            return ''


class QDbgConsole(QTextEdit):
    def __init__(self, parent=None):
        super(QDbgConsole, self).__init__(parent)
        self._buffer = StringIO()
        self.setReadOnly(True)

    def write(self, msg):
        self.insertPlainText(msg)
        self.moveCursor(QTextCursor.End)
        self._buffer.write(msg)

    def __getattr__(self, attr):
        return getattr(self._buffer, attr)


def main():
    app = QApplication(sys.argv)
    window = Main()

    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
