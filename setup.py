#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

if __name__ == "__main__":
    setup(
      name = "setup-release",
      py_modules = ["release"],
      version = "0.0.17.0",
      author = u"Sébastien Boisgérault",
      author_email = "Sebastien.Boisgerault@gmail.com",
      url = "https://pypi.python.org/pypi/release",
      install_requires = ["path.py>=4.3", "sh>=1.09"],
      entry_points = {"distutils.commands": "release = release:Release"},
    )


