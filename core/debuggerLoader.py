import importlib.util
from importlib.abc import Loader, MetaPathFinder
import sys
import os
import core.debugger as debugger

debug = None


class DebugFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if path is None or path == "":
            path = [os.getcwd()]
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue

            return importlib.util.spec_from_file_location(
                fullname, filename,
                loader=DebugLoader(fullname),
                submodule_search_locations=submodule_locations)
        return None


class DebugLoader(Loader):
    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if not debugger.is_source_available(module):
            pass
        else:
            with open(module.__file__, encoding='utf8') as f:
                data = f.read()
            compiled_code = compile(data, module.__file__, 'exec')
            modified_code = debugger.modify_code(compiled_code)
            _globals = vars(module)
            _globals['debug'] = debug
            exec(modified_code, _globals)


def install_custom_loader(debug_function):
    global debug
    debug = debug_function
    sys.meta_path.insert(0, DebugFinder())


def remove_custom_loader():
    del sys.meta_path[0]
