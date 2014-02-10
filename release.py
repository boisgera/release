#!/usr/bin/env python
# coding: utf-8

# Python 2.7 Standard Library
import os
import re
import sys
import xmlrpclib

# Third-Party Libairies
import path # path.py library
import setuptools
import sh

# ------------------------------------------------------------------------------

def printer(line, stdin):
    print line,

class Release(setuptools.Command):

    description = "Manage software releases"

    user_options = [
      ("list", "l", "list package version info"),
      ("pypi", "p", "register/upload on pypi"),
      ("github", "g", "sync git repo with github"),
    ]

    def initialize_options(self):
        self.list = None
        self.pypi = False
        self.github = False

    def finalize_options(self):
        # Boolean options needs to be interpreted explicitely as True or False. 
        # Settings from setup.cfg return string values ; from the command-line,
        # setting an option produces integer value 1 and when it is not set,
        # we end up with None. 
        for option, _, _ in self.user_options:
            if not option.endswith("="): # boolean option (no argument)
                value = getattr(self, option)
                if isinstance(value, str):
                    value = value.lower()
                    if value in ["y", "yes", "t", "true", "on", "1"]:
                        value = True
                    elif value in ["n", "no", "f", "false", "off", "0"]:
                        value = False
                    else:
                        error = "invalid truth value for option {0!r}: {1!r}."
                        error = error.format(option, value)
                        raise ValueError(error)
                else:
                    value = bool(value)
                setattr(self, option, value) 

    def run(self):
        self.name = self.distribution.get_name()
        self.version = self.distribution.get_version()
        if self.list:
            if self.pypi:
                self.display_pypi()
            if self.github:
                self.display_git()
        else:
            if self.check():
                self.update_local_git()
                if self.pypi:
                    self.release_on_pypi()
                if self.github:
                    self.release_on_github()

    def display_pypi(self):
        pypi = xmlrpclib.ServerProxy("http://pypi.python.org/pypi")
        print "current version: {0}".format(self.version)
        visible = pypi.package_releases(self.name)
        releases = pypi.package_releases(self.name, True)
        for i, release in enumerate(releases):
            if not release in visible:
                releases[i] = "({0})".format(release)
        print "Pypi releases: {0}".format(", ".join(releases))

    def display_git(self):
        tags = sh.git("tag").splitlines()
        versions = [tag[1:] for tag in tags if re.match("v[0-9]", tag)]
        versions.reverse()
        print "Git versions: {0}".format(", ".join(versions))

    def check(self):
        if self.pypi:
            self.display_pypi()
        if self.github:
            self.display_git()
        answer = raw_input("Accept ? [Y/n] ")
        answer = answer or "Y"
        return (answer[0].upper() == "Y")        

    def clean(self):
        sudo_setup = getattr(sh.sudo, "./setup.py")
        sudo_setup.clean()
        sh.sudo("rm", "-rf", "dist", "build")
        cwd = path.path(".")
        tmp_files = cwd.files("*~") + cwd.files("*.pyc") 
        sh.sudo("rm", "-rf", *tmp_files)
        egg_infos = cwd.dirs("*.egg-info")
        if egg_infos:
            sh.sudo.rm("-rf", *egg_infos)

    def update_local_git(self):
        self.clean()
        git = sh.git
        short_version = "v{0}".format(self.version)
        long_version = "version {0}".format(self.version)
        git.commit("-a", "-m", long_version, _out=printer)
        git.tag("-a", short_version, "-m", long_version, _out=printer)
        
    def release_on_pypi(self):
        self.clean()
        setup = sh.Command("./setup.py")

        # non-interactive only: use a .pypirc file
        response = setup("register")
        print response
        last_line = str(response).splitlines()[-1]
        if not "(200)" in last_line:
            raise RuntimeError(last_line)

        response = setup("sdist", "upload")
        print response
        last_line = str(response).splitlines()[-1]
        if not "(200)" in last_line:
            raise RuntimeError(last_line)

    def release_on_github(self):
        self.clean()
        git = sh.git
        git.push("--all", _out=printer)
        git.push("--tags", _out=printer)

