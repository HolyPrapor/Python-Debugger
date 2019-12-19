#!/usr/bin/env python3
import sys


def eprint(message):
    print(message, file=sys.stderr)


print("test")
eprint("test2")
print("test3")
eprint("test4")
