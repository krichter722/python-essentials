#!/usr/bin/python
# -*- coding: utf-8 -*- 

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
#    der GNU General Public License, wie von der Free Software Foundation,
#    Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
#    veröffentlichten Version, weiterverbreiten und/oder modifizieren.
#
#    Dieses Programm wird in der Hoffnung, dass es nützlich sein wird, aber
#    OHNE JEDE GEWÄHRLEISTUNG, bereitgestellt; sogar ohne die implizite
#    Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
#    Siehe die GNU General Public License für weitere Details.
#
#    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
#    Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages
import sys
import os
sys.path.append(os.path.realpath(os.path.join(__file__, "..", "lib")))
import python_essentials_globals

setup(
    name = python_essentials_globals.app_name,
    version = python_essentials_globals.app_version_string,
    packages = [python_essentials_globals.app_name, "%s.lib" % (python_essentials_globals.app_name, ), ], # no idea why setuptools.find_packages() doesn't work
    package_dir = {
        python_essentials_globals.app_name: '', 
    },

    # metadata for upload to PyPI
    author = "Karl-Philipp Richter",
    author_email = "krichter722@aol.de",
    description = "Basic python scripts and a wrapper around osm2pqsql which incorporates database creation and associated modularized library functions",
    license = "GPLv3",
    keywords = "OSM postgresql osm2pgsql",
)

