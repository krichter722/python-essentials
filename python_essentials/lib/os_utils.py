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

# manages functions involving all sorts of runtime environments (not only 
# operating systems, like the name suggests, but also script language 
# interpreters)

import os
import sys
import check_os
import subprocess as sp

def which(pgm):
    """replacement for python3's shutil.which"""
    if os.path.exists(pgm) and os.access(pgm,os.X_OK):
        return pgm
    path=os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p,pgm)
        if os.path.exists(p) and os.access(p,os.X_OK):
            return p

def hostname():
    if check_os.check_linux():
        return sp.check_output(["hostname"]).strip().decode("utf-8")
    else:
        raise RuntimeError("operating system not supported")

CHECK_JAVA_NOT_SET = 1
CHECK_JAVA_INVALID = 2

def check_java_valid(java_home=os.getenv("JAVA_HOME")):
    """checks that the `JAVA_HOME` environment variable is set, non-empty and points to a valid Java JDK
    @return `None` if the `JAVA_HOME` variable points to a valid Java JDK`, `CHECK_JAVA_NOT_SET` if `JAVA_HOME` isn't set or empty or `CHECK_JAVA_INVALID` if `JAVA_HOME` doesn't point to a valid Java JDK"""
    if java_home is None or java_home == "":
        return CHECK_JAVA_NOT_SET
    if not os.path.exists(java_home):
        return CHECK_JAVA_INVALID
    java_binary = os.path.join(java_home, "bin/java")
    if not os.path.exists(java_binary):
        return CHECK_JAVA_INVALID

