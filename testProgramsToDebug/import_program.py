#!/usr/bin/env python3

import testProgramsToDebug.helloWorld as helloWorld


def bye_world():
    bye_string = "Bye World!"
    print(bye_string)


helloWorld.hello_world()

bye_world()
