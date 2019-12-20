from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QTextCursor, \
    QColor
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, \
    QApplication, QFileDialog, QMessageBox, QWidget, \
    QVBoxLayout, QTreeView, QTextEdit, QHBoxLayout
from core.editor import Editor, QConditionInputDialog, BACKGROUND_COLOR
import core.debugger as debugger
from PyQt5.QtCore import QCoreApplication, pyqtSignal
import sys
import os
from threading import Thread

STDOUT_COLOR = QColor(255, 255, 255)
STDERR_COLOR = QColor(255, 0, 0)
RUNNING_BG_COLOR = QColor(120, 115, 130)

class GuiDebugger(QMainWindow):
    input_request_handler = pyqtSignal(bool)
    debug_function_handler = pyqtSignal(str, int)
    output_request_handler = pyqtSignal(str, QColor)
    error_request_handler = pyqtSignal(str, QColor)

    def __init__(self, parent=None):
        super(GuiDebugger, self).__init__(parent)
        self.debugger = debugger.Debugger()
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)
        self.tab = TabWidget()
        self.stacktrace_widget = StacktraceWidget()
        self.output_widget = QDbgConsole()
        self.sub_layout = QHBoxLayout()
        self.stdout = OutputProvider(STDOUT_COLOR)
        self.stderr = OutputProvider(STDERR_COLOR)
        self.setup_tab_widget()
        self.set_window_ui()
        self.set_menu()
        self.setup_toolbar()
        self.main_widget.setLayout(self.layout)
        self.sub_layout.addWidget(self.stacktrace_widget)
        self.sub_layout.addWidget(self.output_widget)
        self.layout.addWidget(self.tab)
        self.layout.addLayout(self.sub_layout)
        self.setCentralWidget(self.main_widget)
        self.input = None
        self.active_debugger = False
        self.setup_signals()

    def setup_signals(self):
        self.debug_function_handler.connect(self.highlight_current_line)
        self.debug_function_handler.connect(self.show_stacktrace)
        self.input_request_handler.connect(self.get_input)
        self.output_request_handler.connect(self.write_to_stdout)
        self.error_request_handler.connect(self.write_to_stdout)

    def setup_tab_widget(self):
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

    def setup_toolbar(self):
        self.toolbar = self.addToolBar('Debug actions')
        self.toolbar.addAction(QAction(QIcon('icons/start-debug-icon.svg'),
                                       'Start debugging', self,
                                       triggered=self.start_debugging))
        self.toolbar.addAction(QAction(QIcon('icons/continue-icon.svg'),
                                       'Continue', self, shortcut='F8',
                                       triggered=self.continue_until_breakpoint))
        self.toolbar.addAction(QAction(QIcon('icons/step-in-icon.svg'),
                                       'Make step', self, shortcut='F7',
                                       triggered=self.make_step))
        self.toolbar.addAction(QAction(QIcon('icons/step-over-icon.svg'),
                                       'Step over', self,
                                       triggered=self.step_over))
        self.toolbar.addAction(QAction(QIcon('icons/exec-code-icon.svg'),
                                       'Exec code', self, shortcut='F1',
                                       triggered=self.exec_code))
        self.toolbar.addAction(QAction(QIcon('icons/stop-debug-icon.svg'),
                                       'Stop debug', self,
                                       triggered=self.stop_debug))

    def set_window_ui(self):
        """UI Initialization"""
        self.setWindowTitle("Python debugger")
        self.resize(1000, 500)
        self.setWindowIcon(QIcon('icons/veredit.ico'))
        self.showMaximized()

    def set_menu(self):
        """Menu Initialization"""
        menu = self.menuBar()

        # FILE MENU
        file_menu = menu.addMenu('File')
        file_menu.addAction(QAction(QIcon('icons/open.svg'),
                                    '&Open', self,
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
            self.try_add_tab(file)

    def try_add_tab(self, filename):
        if filename not in self.tab.tab_container:
            file_name = os.path.basename(filename)
            editor = Editor(self, filename, self.add_breakpoint,
                            self.remove_breakpoint)
            with open(filename, 'r') as text:
                self.tab.addTab(editor, file_name)
                editor.setText(text.read())
            self.tab.tab_container[filename] = editor
        self.tab.setCurrentWidget(self.tab.tab_container[filename])

    def _about(self):
        QMessageBox.about(self, 'About Python Debugger', 'Some information')

    def _quit(self):
        QCoreApplication.quit()

    def make_step(self):
        self.debugger.make_step()
        self.set_bg_color(RUNNING_BG_COLOR)

    def step_over(self):
        self.debugger.step_over()
        self.set_bg_color(RUNNING_BG_COLOR)

    def continue_until_breakpoint(self):
        self.debugger.continue_until_breakpoint()
        self.set_bg_color(RUNNING_BG_COLOR)

    def highlight_current_line(self,filename, line_number):
        if len(self.tab.tab_container) > 0:
            if self.tab.currentWidget() is not None:
                self.set_bg_color(QColor(BACKGROUND_COLOR))
                self.tab.currentWidget().clear_highlights()
                self.try_add_tab(filename)
                self.tab.currentWidget().setCursorPosition(
                    line_number - 1, 0)
                self.tab.currentWidget().set_line_highlight(line_number - 1)

    def set_bg_color(self, qcolor):
        if self.tab.currentWidget() is not None:
            self.tab.currentWidget().clear_highlights()
            self.tab.currentWidget().setPaper(qcolor)

    def show_stacktrace(self, *args):
        if self.active_debugger:
            self.stacktrace_widget.importData(self.debugger.current_stacktrace,
                                              self.modify_vars)

    def exec_code(self):
        if self.active_debugger:
            self.debugger.exec_code(QConditionInputDialog(self).readline())

    def add_breakpoint(self, filename, line_num, condition):
        if self.active_debugger:
            self.debugger.add_breakpoint(filename, line_num, condition)

    def modify_vars(self, key, depth, value):
        if self.active_debugger:
            self.debugger.modify_var(depth, key + " = " + value)

    def remove_breakpoint(self, filename, line_num):
        if self.active_debugger:
            self.debugger.remove_breakpoint(filename, line_num)

    def get_input(self):
        self.input = QConditionInputDialog(self).readline()

    def after_debug_func(self):
        print("Program finished.")
        self.stop_debug()

    def stop_debug(self):
        for i in range(len(self.tab.tab_container)):
            self.tab.removeTab(0)
        self.active_debugger = False

    def start_debugging(self):
        if len(self.tab.tab_container) > 0 and not self.active_debugger:
            self.input = None
            self.active_debugger = True
            self.debugger = debugger.Debugger()
            t = Thread(target=self.debugger.start_debugging,
                       args=(debug_function,
                             self.get_current_tab_filename()),
                       kwargs={'stdout': self.stdout,
                               'stderr': self.stderr,
                               'stdin': InputProvider(),
                               'after_debug_func': self.after_debug_func})
            t.daemon = True
            t.start()

    def get_current_tab_filename(self):
        current_widget = self.tab.currentWidget()
        for filename, widget in self.tab.tab_container.items():
            if current_widget == widget:
                return filename
        raise LookupError

    def write_to_stdout(self, message, color):
        self.output_widget.write_with_color(message, color)


def debug_function():
    gui_interface.debug_function_handler.emit(
        gui_interface.debugger.get_filename(),
        gui_interface.debugger.get_line_number())


class InputProvider:
    def readline(self):
        gui_interface.input_request_handler.emit(True)
        while not gui_interface.input:
            pass
        received_input = gui_interface.input
        gui_interface.input = None
        return received_input


class OutputProvider:
    def __init__(self, color: QColor):
        self.color = color

    def write(self, msg):
        gui_interface.output_request_handler.emit(msg, self.color)


class TabWidget(QTabWidget):
    count = 0

    def __init__(self):
        super(TabWidget, self).__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        self.tab_container = dict()

    def addTab(self, widget, filename):
        super(TabWidget, self).addTab(widget, filename)

    def removeTab(self, index):
        tab_to_remove = super(TabWidget, self).widget(index)
        self.tab_container = {filename: tab for filename, tab
                              in self.tab_container.items()
                              if tab != tab_to_remove}
        super(TabWidget, self).removeTab(index)


class StacktraceWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.tree = QTreeView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Level', 'Values'])
        self.tree.header().setDefaultSectionSize(180)
        self.tree.setModel(self.model)

    def importData(self, data, signal_func):
        self.model.setRowCount(0)
        root = self.model.invisibleRootItem()
        for index, stack_values in enumerate(data):
            parent = QStandardItem(str(index + 1))
            parent.setEditable(False)
            for key, value in stack_values.f_locals.items():
                keyWidget = QStandardItem(str(key))
                keyWidget.setEditable(False)
                # valueWidget = ValueWidget(str(value), str(key), str(index))
                # valueWidget.change_call.connect(signal_func) Doesn't work yet
                parent.appendRow([keyWidget,
                                  QStandardItem(str(value))])
            root.appendRow(parent)


class ValueWidget(QStandardItem):
    change_call = pyqtSignal(object, object, object)

    def __init__(self, value, key, depth):
        super(QStandardItem, self).__init__(value)
        self.key = key
        self.depth = depth

    def setData(self, *args, **kwargs):
        super(self).setData(*args, **kwargs)
        self.change_call.emit(self.key, self.depth, self.data())


class QDbgConsole(QTextEdit):
    def __init__(self, parent=None):
        super(QDbgConsole, self).__init__(parent)
        self.setReadOnly(True)

    def write_with_color(self, msg, color):
        previous_color = self.textColor()
        self.setTextColor(color)
        self.insertPlainText(msg)
        self.setTextColor(previous_color)
        self.moveCursor(QTextCursor.End)


def main():
    global gui_interface
    app = QApplication(sys.argv)
    window = GuiDebugger()

    gui_interface = window
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
