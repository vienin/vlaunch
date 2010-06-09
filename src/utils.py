# -*- coding: utf-8 -*-

# UFO-launcher - A multi-platform virtual machine launcher for the UFO OS
#
# Copyright (c) 2008-2009 Agorabox, Inc.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. 


import logging
import logging.handlers
import sys
if sys.platform == "win32": import subprocess
else: import ufo_subprocess as subprocess
import os, os.path


class SmartDict(dict):
    def __init__(self):
        super(SmartDict, self).__init__(self)
        self.on_del_item_callbacks = []
        self.on_set_item_callbacks = []

    def register_on_del_item_callback(self, callback):
        if callback not in self.on_del_item_callbacks:
            self.on_del_item_callbacks.append(callback)

    def register_on_set_item_callback(self, callback):
        if callback not in self.on_set_item_callbacks:
            self.on_set_item_callbacks.append(callback)

    def __setitem__(self, key, value):
        super(SmartDict, self).__setitem__(key, value)
        for callback in  self.on_set_item_callbacks:
            callback(key, value)

    def __delitem__(self, key):
        super(SmartDict, self).__delitem__(key)
        for callback in  self.on_del_item_callbacks:
            callback(key)


class RoolOverLogger():
    
    format = "%(asctime)s [%(levelname)s] %(message)s"
    
    def __init__(self, file_path, count):
        do_roolover = os.path.exists(file_path)
        self.file_handler = logging.handlers.RotatingFileHandler(file_path, backupCount=count)
        self.file_handler.setFormatter(logging.Formatter(self.format))
        self.file_handler.setLevel(logging.DEBUG)

        if do_roolover:
            self.file_handler.doRollover()

        self.logger = logging.getLogger(os.path.basename(file_path))
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.file_handler)

    def debug(self, msg):
        self.logger.debug(msg)

    def safe_debug(self, msg):
        try:
            self.logger.debug(msg)
        except:
            pass


def grep(input, pattern, inverse=False):
    for line in input.split("\n"):
        if inverse:
            if pattern not in line:
                return line
        else:
            if pattern in line:
                return line
    return ""

def append_to_end(filename, line):
    if not path.exists(filename):
        lines = [ ]
    else:
        lines = open(filename).readlines()
    if lines and not lines[-1].strip():
        line += "\n" + line
    open(filename, 'a').write(line)

try:
    from PyQt4 import QtCore_ # This 'backend' was supposed to work...
    def call(cmds, env = None, shell = False, cwd = None, output = False):
        if type(cmds[0]) == str:
            cmds = [ cmds ]
        lastproc = None
        procs = []
        for cmd in cmds:
            proc = QtCore.QProcess()
            if cwd:
                proc.setWorkingDirectory = cwd
            if env:
                proc.setEnvironment(env)
            if lastproc:
                lastproc.setStandardOutputProcess(proc)
            lastproc = proc
            procs.append((proc, cmd))

        for proc, cmd in procs:
            proc.start(cmd[0], cmd[1:])
        
        success = lastproc.waitForFinished(-1)
        if success:
            if output:
                return proc.exitCode(), proc.readAllStandardOutput()
            return proc.exitCode()
        return -1

except:
    def call(cmds, env = None, shell = False, cwd = None, output = False, input = None, fork=True, spawn=False, log=True, preexec_fn=None):
        if type(cmds[0]) == str:
            cmds = [ cmds ]
        lastproc = None
        for i, cmd in enumerate(cmds):
            if log: logging.debug(" ".join(cmd) + " with environment : " + str(env))
            if lastproc:
                stdin = lastproc.stdout
            else:
                stdin = None
            stdout = None
            preexec_fn_ = None
            if (len(cmds) and i != len(cmds) - 1):
                stdout = subprocess.PIPE
            if output and i == len(cmds) - 1:
                stdout = subprocess.PIPE
                preexec_fn_ = preexec_fn
            if fork:
                proc = subprocess.Popen(cmd, env=env, shell=shell, cwd=cwd, stdin=stdin, stdout=stdout, preexec_fn=preexec_fn_)
            else:
                proc = subprocess.Popen(cmd, env=env, shell=shell, cwd=cwd, stdin=stdin, stdout=stdout, preexec_fn_=preexec_fn_, fork=fork)
            lastproc = proc

        if spawn:
            return lastproc
        elif output or len(cmds) > 1:
            output = lastproc.communicate()[0]
            if log: logging.debug("Returned : " + str(lastproc.returncode))
            return lastproc.returncode, output
        elif input:
            lastproc.communicate(input)[0]
            if log: logging.debug("Returned : " + str(lastproc.returncode))
            return lastproc.returncode
        else:
            retcode = lastproc.wait()
            if log: logging.debug("Returned : " + str(retcode))
            return retcode

def relpath(path, start=os.path.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [os.path.pardir] * (len(start_list)-i) + path_list[i:]   
    if not rel_list:
        return os.path.curdir
    return os.path.join(*rel_list)

def get_free_space(path):
    stats = os.statvfs(path)
    return stats.f_bavail * stats.f_bsize

