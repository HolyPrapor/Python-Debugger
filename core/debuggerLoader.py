from importlib import invalidate_caches
import importlib.util
from importlib.abc import Loader, MetaPathFinder
import sys
import os
import core.debugger as debugger


class DebugFinder(MetaPathFinder):
    def __init__(self):
        self.loaded_modules = []

    def invalidate_caches(self):
        for module in self.loaded_modules:
            if module in sys.modules:
                del sys.modules[module]

    def find_spec(self, fullname, path, target=None):
        if path is None or path == "":
            path = [os.getcwd()]
            #for entry in sys.path:
             #   path.append(entry)
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

            self.loaded_modules.append(fullname)

            return importlib.util.spec_from_file_location(
                fullname, filename,
                loader=DebugLoader(fullname),
                submodule_search_locations=submodule_locations)
        return None


class DebugLoader(Loader):
    debug = None

    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if not debugger.is_source_available(module):
            pass
        else:
            with open(module.__file__, 'r') as f:
                data = f.read()
            compiled_code = compile(data, module.__file__, 'exec')
            modified_code = debugger.modify_code(compiled_code)
            _globals = vars(module)
            _globals['debug'] = DebugLoader.debug
            try:
                exec(modified_code, _globals)
            except:
                print(sys.exc_info(), file=sys.stderr)


def install_custom_loader(debug_function):
    DebugLoader.debug = debug_function
    sys.meta_path.insert(0, DebugFinder())


def remove_custom_loader_and_invalidate_caches():
    invalidate_caches()
    del sys.meta_path[0]
