#!/usr/bin/env python
# coding: utf-8

# Python 2.7 Standard Library
import ConfigParser
import os
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
            self.display_package_info()
        else:
            if self.pypi:
                self.release_on_pypi()
            if self.github:
                self.release_on_github()

    # This is Pypi package info to be honest ... rename and don't use
    # unless pypi is selected.
    def display_package_info(self):
        pypi = xmlrpclib.ServerProxy("http://pypi.python.org/pypi")
        print "current version: {0}".format(self.version)
        releases = pypi.package_releases(self.name) # shows visible only
        print "Pypi releases: {0}".format(", ".join(releases))

    def check(self):
        self.display_package_info()
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
        git.commit("-a", "-m", long_version)
        git.tag("-a", short_version, "-m", long_version)
        git.push("--tags")

    def release_on_github(self):
        pass


