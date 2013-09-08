#!/usr/bin/env python
# coding: utf-8

# Python 2.7 Standard Library
import os
import re
import xmlrpclib

# Third-Party Libairies
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
        # TODO: distinguish local version and version uploaded on GitHub ?
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

    def release_on_pypi(self):
        if self.check():
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

    def release_on_github(self):
        git = sh.git
        short_version = "v{0}".format(self.version)
        long_version = "version {0}".format(self.version)
        print git.commit("-a", "-m", long_version)
        print git.push()
        print git.tag("-a", short_version, "-m", long_version)
        print git.push("--tags")



