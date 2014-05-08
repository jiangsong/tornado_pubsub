#!/usr/bin/env python
# coding=utf-8

#
# Copyright 2013 nava
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__author__ = 'nava'
import os
import sys

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

EXTRA_PATHS = [
    DIR_PATH,
    os.path.join(DIR_PATH, 'lib', 'tornado-3.1'),
    os.path.join(DIR_PATH, 'lib', 'blinker-1.3'),
    os.path.join(DIR_PATH, 'lib', 'tornado-redis-2.4.7'),
]

def fix_sys_path(extra_extra_paths=()):
    """
    @summary: Fix the sys.path to include our extra paths.
    """
    extra_paths = EXTRA_PATHS[:]
    extra_paths.extend(extra_extra_paths)
    sys.path = extra_paths + sys.path

def main(args):
    """
    @summary: the main program

    @since 0.13.8.24
    """
    fix_sys_path()
    script_path = os.path.join(DIR_PATH, "app.py")
    execfile(script_path, globals())

if __name__ == '__main__':
    main(sys.argv)