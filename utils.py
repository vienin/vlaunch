import logging
import subprocess
import conf
import os.path as path
import shutil

def grep(input, pattern, inverse=False):
    for line in input.split("\n"):
        if inverse:
            if pattern not in line:
                return line
        else:
            if pattern in line:
                return line
    return ""
    
def call(cmd, env = None, shell = False, cwd = None):
    logging.debug(" ".join(cmd) + " with environment : " + str(env))
    retcode = subprocess.call(cmd, env = env, shell = shell, cwd = cwd)
    logging.debug("Returned : " + str(retcode))
    return retcode

def find_network_device():
    if not conf.HOSTNET:
        return conf.NET_NAT
    return conf.NET_HOST

def write_fake_vmdk(dev):
    vmdk = path.join(conf.HOME, "HardDisks", conf.VMDK)
    shutil.copyfile(path.join(conf.HOME, "HardDisks", "fake.vmdk"), vmdk)

def append_to_end(filename, line):
    if not path.exists(filename):
        lines = [ ]
    else:
        lines = open(filename).readlines()
    if lines and not lines[-1].strip():
        line += "\n" + line
    open(filename, 'a').write(line)
