from importlib import invalidate_caches
from importlib.abc import Loader
from importlib.machinery import FileFinder
import sys
import core.debugger as debugger

debug = None


class DebugLoader(Loader):
    def __init__(self, filename, path):
        self.filename = filename
        self.path = path

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(module.__file__, encoding='utf8') as f:
            data = f.read()
        compiled_code = compile(data, module.__file__, 'exec')
        modified_code = debugger.modify_code(compiled_code)
        _globals = vars(module)
        _globals['debug'] = debug
        _globals['__name__'] = '__main__'
        exec(modified_code, _globals)  # if globals[debug] = self.debug
        # ... ? if compile filename is not exact ?


def install_custom_loader(debug_function):
    global debug
    debug = debug_function
    loader_details = DebugLoader, [".py"]
    sys.path_hooks.insert(0, FileFinder.path_hook(loader_details))
    sys.path_importer_cache.clear()
    invalidate_caches()
