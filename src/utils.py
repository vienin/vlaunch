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
import subprocess

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
    def call(cmds, env = None, shell = False, cwd = None, output = False, input = None, fork=True, spawn=False, log=True):
        if type(cmds[0]) == str:
            cmds = [ cmds ]
        lastproc = None
        procs = []
        for i, cmd in enumerate(cmds):
            if log: logging.debug(" ".join(cmd) + " with environment : " + str(env))
            if lastproc:
                stdin = lastproc.stdout
            else:
                stdin = None
            stdout = None
            if (len(cmds) and i != len(cmds) - 1):
                stdout = subprocess.PIPE
            if output and i == len(cmds) - 1:
                stdout = subprocess.PIPE
            if fork:
                proc = subprocess.Popen(cmd, env=env, shell=shell, cwd=cwd, stdin=stdin, stdout=stdout)
            else:
                proc = subprocess.Popen(cmd, env=env, shell=shell, cwd=cwd, stdin=stdin, stdout=stdout, fork=fork)
            lastproc = proc

        if spawn:
            return lastproc
        elif output or len(cmds) > 1:
            output = lastproc.communicate()[0]
            logging.debug("Returned : " + str(lastproc.returncode))
            return lastproc.returncode, output
        elif input:
            lastproc.communicate(input)[0]
            logging.debug("Returned : " + str(lastproc.returncode))
            return lastproc.returncode
        else:
            retcode = lastproc.wait()
            logging.debug("Returned : " + str(retcode))
            return retcode
