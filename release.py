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
        # values extracted from 'setup.cfg' are strings
        if isinstance(self.pypi, str):
            self.pypi = eval(self.pypi)
        if isinstance(self.github, str):
            self.github = eval(self.github)

    def run(self):
        self.name = self.distribution.get_name()
        self.version = self.distribution.get_version()
        if self.list:
            if self.pypi:
                self.display_pypi()
            if self.github:
                self.display_git()
        else:
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

    def release_on_pypi(self):
        if self.check():
            self.clean()
            setup = sh.Command("./setup.py")

            # needs to be non-interactive: use a .pypirc file
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

# BUG: for some reason, getting stuck in this function. Uhu ? One-by-one,
#      it works ?
    def release_on_github(self):
        if self.check():
            self.clean()
            git = sh.git
            short_version = "v{0}".format(self.version)
            long_version = "version {0}".format(self.version)
            print "---"
            try:
                git.commit("-a", "-m", long_version)
            except sh.ErrorReturnCode as error:
                if not "nothing to commit" in error.stdout:
                    sys.exit(error.stdout)
            print "*" # STUCK IN THE PUSH ... transfrom into some iter version ?
            # to see if there is a message ? Maybe that's a root id pb. Seems so.
            # So we should detect it ? But then what should we do ? Because it 
            # can make sense for when --pypi is on to be root (to access metadata).
            # Also, if the repo was not obtain with ssh, git may be asking for a
            # password to accept the push ...
            print git.push()
            print "**"
            print git.tag("-a", short_version, "-m", long_version)
            print "***"
            print git.push("--tags")
            print "****"


