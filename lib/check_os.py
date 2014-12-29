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

import subprocess as sp
import re
import os
import sys

# constants
ARCHITECTURE_X86_64 = "x86_64"
ARCHITECTURE_I386 = "i386"
ARCHITECTURE_I686 = "i686"
INSTRUCTION_SET_AMD64 = "amd64"
INSTRUCTION_SET_I386 = "i386"
ARCHITECTURE_INSTRUCTION_SET_DICT = {
    ARCHITECTURE_X86_64: INSTRUCTION_SET_AMD64,
    ARCHITECTURE_I386: INSTRUCTION_SET_I386,
    ARCHITECTURE_I686: INSTRUCTION_SET_I386,
}

# binaries
lsb_release = "lsb_release"

def check_linux():
    if not check_python3():
        ret_value = sys.platform == "linux2"
        return ret_value
    else:
        ret_value = sys.platform == "linux"
        return ret_value

def check_opensuse():
    try:
        lsb_release_id_short = sp.check_output([lsb_release, "-d", "-s"])
        return "openSUSE" in lsb_release_id_short
    except Exception:
        return False

def check_ubuntu():
    try:
        lsb_release_id_short = sp.check_output([lsb_release, "-d", "-s"]).strip().decode("utf-8")
        ret_value = "Ubuntu" in lsb_release_id_short
        return ret_value
    except Exception:
        return False

def check_debian():
    try:
        lsb_release_id_short = sp.check_output([lsb_release, "-d", "-s"]).strip().decode("utf-8")
        ret_value = "Debian" in lsb_release_id_short
        return ret_value
    except Exception:
        return False

def check_linuxmint():
    try:
        lsb_release_id_short = sp.check_output([lsb_release, "-d", "-s"]).strip().decode("utf-8")
        ret_value = "Linux Mint" in lsb_release_id_short
        return ret_value
    except Exception:
        return False

def check_root():
    uid = sp.check_output(["id","-u"]).strip()
    ret_value = int(uid) == 0
    return ret_value

# @return <code>True</code> if the python version is >= 3.0, otherwise <code>False</code>
def check_python3():
    ret_value = sys.version_info >= (3,0)
    return ret_value

def findout_architecture():
    architecture = sp.check_output(["uname","-m"]).strip()
    return architecture

def findout_instruction_set():
    architecture = findout_architecture()
    instruction_set = ARCHITECTURE_INSTRUCTION_SET_DICT[architecture]
    return instruction_set

#lsb_release only works with python2.x
def findout_release_ubuntu():
    while not os.path.isfile("/usr/bin/python2.6") and not os.path.isfile("/usr/bin/python2.7"):
        print("Neither python2.6 nor python 2.7 could be found in /usr/bin/. It's necessary to determine your distribution release")
        confirm("proceed","Install python 2.6 or 2.7 and make it available at /usr/bin/python2.6 or /usr/lib/python2.7")
    release= sp.check_output([lsb_release,"-cs"]).strip().decode("utf-8")
    return release

def findout_release_debian():
    return findout_release_ubuntu()

# useful is a feature is available for any version up from a certain (the tuple contains ints because strings are less comparable)
def findout_release_ubuntu_tuple():
    while not os.path.isfile("/usr/bin/python2.6") and not os.path.isfile("/usr/bin/python2.7"):
        print("Neither python2.6 nor python 2.7 could be found in /usr/bin/. It's necessary to determine your distribution release")
        confirm("proceed","Install python 2.6 or 2.7 and make it available at /usr/bin/python2.6 or /usr/lib/python2.7")
    release_number = sp.check_output([lsb_release, "-rs"]).strip().decode("utf-8")
    release_tuple = tuple([int(x) for x in release_number.split(".")])
    return release_tuple

# linuxmint release identifiers are natural numbers
def findout_release_linuxmint():
    ret_value = sp.check_output([lsb_release, "-r", "-s"]).decode("utf-8").strip()
    return int(ret_value)

