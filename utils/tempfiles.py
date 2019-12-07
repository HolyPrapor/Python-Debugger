import os
import tempfile


class TempFiles:
    def __init__(self, amount):
        self.amount = amount

    def __enter__(self):
        self.files = []
        for _ in range(self.amount):
            self.files.append(tempfile.NamedTemporaryFile(delete=False,
                                                          suffix='.py'))
        return self.files

    def __exit__(self, exc_type, exc_val, exc_tb):
        for file in self.files:
            try:
                file.close()
                os.remove(file.name)
            except OSError:
                pass
        return False
