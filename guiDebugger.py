from PyQt5.QtGui import (
    QIcon,
    QStandardItem,
    QStandardItemModel,
    QTextCursor,
    QColor,
)
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QTabWidget,
    QApplication,
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QTreeView,
    QTextEdit,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QPushButton,
)
from core.editor import Editor, BACKGROUND_COLOR
import core.debugger as debugger
from PyQt5.QtCore import QCoreApplication, pyqtSignal
import sys
import os
from threading import Thread
import inspect
import types
import collections

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)
)

STDOUT_COLOR = QColor(0, 0, 0)
STDERR_COLOR = QColor(255, 0, 0)
RUNNING_BG_COLOR = QColor(120, 115, 130)


class MainWindow(QMainWindow):
    input_request_handler = pyqtSignal()
    debug_function_handler = pyqtSignal(str, int)
    output_request_handler = pyqtSignal(str, QColor)
    error_request_handler = pyqtSignal(str, QColor)
    after_debug_function_handler = pyqtSignal()

    def __init__(self, debug_function, parent=None):
        super().__init__(parent)
        self.debug_function = debug_function
        self.debugger = debugger.Debugger()
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)
        self.tab = TabWidget()
        self.stacktrace_widget = StacktraceWidget(self)
        self.output_widget = QDbgConsole()
        self.sub_layout = QHBoxLayout()
        self.stdin = InputProvider(self)
        self.stdout = OutputProvider(self, STDOUT_COLOR)
        self.stderr = OutputProvider(self, STDERR_COLOR)
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
        self.input = collections.deque()
        self.providing_input = False
        self.active_debugger = False
        self.setup_signals()
        self.last_launch_info = dict()

    def setup_signals(self):
        self.debug_function_handler.connect(self.highlight_current_line)
        self.debug_function_handler.connect(self.show_stacktrace)
        self.input_request_handler.connect(self.get_input)
        self.output_request_handler.connect(self.write_to_stdout)
        self.error_request_handler.connect(self.write_to_stdout)
        self.after_debug_function_handler.connect(self.stop_debug)

    def setup_tab_widget(self):
        path = os.path.dirname(os.path.abspath(__file__))
        close_button_hover_image = os.path.join(path, "icons/close_hover.svg")
        close_button_image = os.path.join(path, "icons/close.svg")
        self.tab.setStyleSheet(
            """
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
            image: url(%s)
        }
        QTabBar::close-button:hover {
            image: url(%s)
        }
        """
            % (close_button_hover_image, close_button_image)
        )

    def setup_toolbar(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self.toolbar = self.addToolBar("Debug actions")
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/start-debug-icon.svg")),
                "Start debugging",
                self,
                shortcut="F5",
                triggered=self.start_debugging,
            )
        )
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/continue-icon.svg")),
                "Continue",
                self,
                shortcut="F9",
                triggered=self.continue_until_breakpoint,
            )
        )
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/step-in-icon.svg")),
                "Step in",
                self,
                shortcut="F7",
                triggered=self.make_step,
            )
        )
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/step-over-icon.svg")),
                "Step over",
                self,
                shortcut="F8",
                triggered=self.step_over,
            )
        )
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/exec-code-icon.svg")),
                "Exec code",
                self,
                shortcut="F6",
                triggered=self.exec_code,
            )
        )
        self.toolbar.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/stop-debug-icon.svg")),
                "Stop debug",
                self,
                shortcut="F3",
                triggered=self.stop_debug,
            )
        )

    def set_window_ui(self):
        """UI Initialization"""
        path = os.path.dirname(os.path.abspath(__file__))
        self.setWindowTitle("Python debugger")
        self.resize(1000, 500)
        self.setWindowIcon(QIcon(os.path.join(path, "icons/veredit.ico")))
        self.showMaximized()

    def set_menu(self):
        """Menu Initialization"""
        path = os.path.dirname(os.path.abspath(__file__))
        menu = self.menuBar()
        # FILE MENU
        file_menu = menu.addMenu("File")
        file_menu.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/open.svg")),
                "&Open",
                self,
                shortcut="Ctrl+O",
                triggered=self._open_file,
            )
        )
        file_menu.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/power.svg")),
                "&Quit",
                self,
                shortcut="Ctrl+Q",
                triggered=self._quit,
            )
        )

        # HELP MENU
        help_menu = menu.addMenu("&Help")
        help_menu.addAction(
            QAction(
                QIcon(os.path.join(path, "icons/info.svg")),
                "&Info",
                self,
                shortcut="F1",
                triggered=self._about,
            )
        )

    def _open_file(self):
        """Open file and set it in a new tab or in current if tab is empty"""
        file = QFileDialog.getOpenFileName(self, "Open file", ".")[0]
        if file:
            self.try_add_tab(file)

    def try_add_tab(self, filename):
        if filename not in self.tab.tab_container:
            file_name = os.path.basename(filename)
            editor = Editor(
                self, filename, self.add_breakpoint, self.remove_breakpoint
            )
            with open(filename, "r") as text:
                self.tab.addTab(editor, file_name)
                editor.setText(text.read())
            self.tab.tab_container[filename] = editor
        self.tab.setCurrentWidget(self.tab.tab_container[filename])

    def _about(self):
        QMessageBox.about(
            self,
            "About Python Debugger",
            "Ctrl + O : Open file\n"
            "F5 : Launch debugger on current opened file\n"
            "F7 : Step in\n"
            "F8 : Step over\n"
            "F9 : Continue\n"
            "F6 : Exec code\n"
            "F3 : Stop debugger\n"
            "Ctrl + Q : Exit debugger\n"
            "Editing stack values allowed through stack widget\n"
            "To place a breakpoint click near the line number\n"
            "To place a conditional breakpoint click while "
            "holding SHIFT button",
        )

    def _quit(self):
        QCoreApplication.quit()

    def make_step(self):
        if self.active_debugger:
            self.debugger.make_step()
            self.set_bg_color(RUNNING_BG_COLOR)

    def step_over(self):
        if self.active_debugger:
            self.debugger.step_over()
            self.set_bg_color(RUNNING_BG_COLOR)

    def continue_until_breakpoint(self):
        if self.active_debugger:
            self.debugger.continue_until_breakpoint()
            self.set_bg_color(RUNNING_BG_COLOR)

    def highlight_current_line(self, filename, line_number):
        if len(self.tab.tab_container) > 0:
            if self.tab.currentWidget() is not None:
                self.set_bg_color(QColor(BACKGROUND_COLOR))
                self.tab.currentWidget().clear_highlights()
                self.try_add_tab(filename)
                self.tab.currentWidget().setCursorPosition(line_number - 1, 0)
                self.tab.currentWidget().set_line_highlight(line_number - 1)

    def set_bg_color(self, qcolor):
        for index in range(len(self.tab.tab_container)):
            widget = self.tab.widget(index)
            widget.clear_highlights()
            widget.setPaper(qcolor)

    def show_stacktrace(self):
        if self.active_debugger:
            self.stacktrace_widget.importData(self.debugger.current_stacktrace)

    def exec_code(self):
        if self.active_debugger:
            self.debugger.exec_code(
                QBigInputDialog(
                    self, "Exec code", "Write your code to launch:"
                ).readlines()
            )
            self.show_stacktrace()

    def add_breakpoint(self, filename, line_num, condition):
        if self.active_debugger:
            self.debugger.add_breakpoint(filename, line_num, condition)

    def modify_vars(self, key, depth, value):
        if self.active_debugger:
            self.debugger.modify_var(depth, key + " = " + value)
            self.show_stacktrace()

    def remove_breakpoint(self, filename, line_num):
        if self.active_debugger:
            self.debugger.remove_breakpoint(filename, line_num)

    def get_input(self):
        while len(self.input) == 0 and not self.providing_input:
            self.providing_input = True
            lines = QBigInputDialog(
                self, "Input dialog", "Write your input"
            ).readlines()
            if lines:
                for line in lines.split():
                    self.input.append(line)
            self.providing_input = False

    def set_breakpoints_from_tabs(self):
        if self.active_debugger:
            for index in range(len(self.tab.tab_container)):
                widget = self.tab.widget(index)
                for bp in widget.breakpoints:
                    self.debugger.add_breakpoint(
                        bp.filename, bp.line_number, bp.condition
                    )

    def after_debug_func(self):
        if self.active_debugger:
            print("Program finished.")
            self.after_debug_function_handler.emit()

    def clear_tabs(self):
        for i in range(len(self.tab.tab_container)):
            self.tab.removeTab(0)

    def stop_debug(self):
        self.active_debugger = False
        for index in range(len(self.tab.tab_container)):
            widget = self.tab.widget(index)
            widget.clear_highlights()
            widget.setPaper(QColor(BACKGROUND_COLOR))
        if self.debugger:
            self.debugger.stop_debug()
        self.debugger = None

    def start_debugging(self):
        if not self.active_debugger:
            (
                program_to_debug,
                working_directory,
                arguments,
            ) = StartProgramDialog(self).get_inputs()
            if program_to_debug and os.path.isfile(program_to_debug):
                if not working_directory:
                    working_directory = os.path.dirname(program_to_debug)
                self.try_add_tab(program_to_debug)
                self.input = collections.deque()
                self.providing_input = False
                self.active_debugger = True
                self.debugger = debugger.Debugger()
                self.set_breakpoints_from_tabs()
                t = Thread(
                    target=self.debugger.start_debugging,
                    args=(self.debug_function, program_to_debug),
                    kwargs={
                        "stdout": self.stdout,
                        "stderr": self.stderr,
                        "stdin": self.stdin,
                        "after_debug_func": self.after_debug_func,
                        "new_wd": working_directory,
                        "arguments": arguments.split(),
                    },
                )
                t.daemon = True
                t.start()
                self.last_launch_info[program_to_debug] = (
                    program_to_debug,
                    working_directory,
                    arguments,
                )
            elif program_to_debug or working_directory or arguments:
                self.write_to_stdout(
                    "Path to file or WD was incorrect\n", STDERR_COLOR
                )

    def get_current_tab_filename(self):
        current_widget = self.tab.currentWidget()
        for filename, widget in self.tab.tab_container.items():
            if current_widget == widget:
                return filename
        return None

    def write_to_stdout(self, message, color):
        self.output_widget.write_with_color(message, color)


class InputProvider:
    def __init__(self, parent):
        self.parent = parent

    def readline(self):
        if len(self.parent.input) == 0 and not self.parent.providing_input:
            self.parent.input_request_handler.emit()
        while len(self.parent.input) == 0:
            pass
        received_input = self.parent.input.popleft()
        return received_input


class OutputProvider:
    def __init__(self, parent, color: QColor):
        self.parent = parent
        self.color = color

    def write(self, msg):
        self.parent.output_request_handler.emit(msg, self.color)


class TabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.setDocumentMode(True)
        self.setUsesScrollButtons(True)
        self.tab_container = dict()

    def addTab(self, widget, filename):
        super().addTab(widget, filename)

    def removeTab(self, index):
        tab_to_remove = super().widget(index)
        self.tab_container = {
            filename: tab
            for filename, tab in self.tab_container.items()
            if tab != tab_to_remove
        }
        super().removeTab(index)


class StacktraceWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.tree = QTreeView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Level", "Values"])
        self.tree.header().setDefaultSectionSize(180)
        self.tree.setModel(self.model)

    def importData(self, data):
        self.model.setRowCount(0)
        root = self.model.invisibleRootItem()
        for index, stack_values in enumerate(data):
            parent = QStandardItem(
                str(stack_values.f_code.co_name)
                + str(
                    inspect.signature(
                        types.FunctionType(stack_values.f_code, {})
                    )
                )
            )
            parent.setEditable(False)
            for key, value in stack_values.f_locals.items():
                keyWidget = QStandardItem(str(key))
                keyWidget.setEditable(False)
                try:
                    value_as_str = repr(value)
                except BaseException:
                    value_as_str = "Can't see"
                valueWidget = ValueWidget(
                    self.parent, value_as_str, str(key), str(index)
                )
                parent.appendRow([keyWidget, valueWidget])
            root.appendRow(parent)


class ValueWidget(QStandardItem):
    def __init__(self, global_parent, value, key, depth):
        super().__init__(value)
        self.global_parent = global_parent
        self.key = key
        self.depth = depth

    def setData(self, value, role):
        super().setData(value, role)
        self.global_parent.modify_vars(self.key, int(self.depth), value)


class QDbgConsole(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def write_with_color(self, msg, color):
        previous_color = self.textColor()
        self.setTextColor(color)
        self.insertPlainText(msg)
        self.setTextColor(previous_color)
        self.moveCursor(QTextCursor.End)


class QBigInputDialog:
    def __init__(self, parentWidget, title, label):
        self.parentWidget = parentWidget
        self.title = title
        self.label = label

    def readlines(self):
        text, ok = QInputDialog.getMultiLineText(
            self.parentWidget, self.title, self.label
        )
        if ok:
            return str(text)
        else:
            return ""


class StartProgramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.path_to_program = QLineEdit(self)
        self.path_to_program_dialog_button = QPushButton(self)
        self.path_to_program_dialog_button.setText("Open File")
        self.working_directory = QLineEdit(self)
        self.working_directory_dialog_button = QPushButton(self)
        self.working_directory_dialog_button.setText("Open Directory")
        self.arguments = QLineEdit(self)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )

        layout = QFormLayout(self)
        layout.addRow("Path to program", self.path_to_program)
        layout.addRow(self.path_to_program_dialog_button)
        layout.addRow("Working directory", self.working_directory)
        layout.addRow(self.working_directory_dialog_button)
        layout.addRow("Arguments", self.arguments)
        layout.addWidget(buttonBox)

        self.setFixedSize(640, 200)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.path_to_program_dialog_button.clicked.connect(self.get_filename)
        self.working_directory_dialog_button.clicked.connect(
            self.get_directory
        )
        if parent:
            current_tab_filename = parent.get_current_tab_filename()
            if (
                current_tab_filename
                and current_tab_filename in parent.last_launch_info
            ):
                (path, wd, arguments) = parent.last_launch_info[
                    current_tab_filename
                ]
                self.path_to_program.setText(path)
                self.working_directory.setText(wd)
                self.arguments.setText(arguments)
            elif current_tab_filename:
                self.path_to_program.setText(current_tab_filename)
                working_directory = os.path.dirname(current_tab_filename)
                self.working_directory.setText(working_directory)

    def get_inputs(self):
        result = self.exec()
        if result:
            return (
                self.path_to_program.text(),
                self.working_directory.text(),
                self.arguments.text(),
            )
        return None, None, None

    def get_filename(self):
        filename, ok = QFileDialog.getOpenFileName(self, "Select file")
        if ok:
            self.path_to_program.setText(filename)

    def get_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select folder")
        if directory:
            self.working_directory.setText(directory)


class GuiDebugger:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow(self.debug_function)

    def debug_function(self):
        self.window.debug_function_handler.emit(
            self.window.debugger.get_filename(),
            self.window.debugger.get_line_number(),
        )


def main():
    gui_debugger = GuiDebugger()
    gui_debugger.window.show()
    sys.exit(gui_debugger.app.exec_())


if __name__ == "__main__":
    main()
