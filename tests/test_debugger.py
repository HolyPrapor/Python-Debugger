#!/usr/bin/env python3

import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
import core.debugger


class DebuggerTests(unittest.TestCase):
    def test_debugger_logic(self):
        self.assertEqual(True, True)
