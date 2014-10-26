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

import file_line_utils
import subprocess
import os

##############################
# user and group tools 
##############################

# @return the username associated with the specified id (as listed in /etc/passwd) or <tt>None</tt> if there's no such uid
# can be done with <code>id -u -n <uid></code>, but this is buggy in OpenSUSE due to missing services (as so many other commands)
def username_by_id(uid):
    if str(type(uid)) != "<type 'int'>":
        raise ValueError("uid has to be an int")
    passwd_lines = file_line_utils.file_lines("/etc/passwd", "#")
    for passwd_line in passwd_lines:
        passwd_line_content = passwd_line.split(":")
        if int(passwd_line_content[2]) == uid:
            return passwd_line_content[0]
    return None

def groupname_by_id(gid):
    if str(type(uid)) != "<type 'int'>":
        raise ValueError("uid has to be an int")
    passwd_lines = file_line_utils.file_files("/etc/passwd", "#")
    for passwd_line in passwd_lines:
        passwd_line_content = passwd_line.split(":")
        if (passwd_line_content[3]) == gid:
            return passwd_line_content[0]
    return None

# @return the effective gid or <code>-1</code> if group <tt>groupname</tt> doesn't exist
def id_by_username(username):
    if not check_user_exists(username):
        return -1
    ret_value = subprocess.check_output(["id", "-u", username])
    return int(ret_value)

# @return the effective gid or <code>-1</code> if group <tt>groupname</tt> doesn't exist
def id_by_groupname(groupname):
    if not check_group_exists(groupname):
        return -1
    group_lines = file_line_utils.file_lines("/etc/group", comment_symbol="#")
    for group_line in group_lines:
        group_line_content = group_line.split(":")
        if (group_line_content[0]) == groupname:
            return int(group_line_content[2])
    return None
# implementation notes:
# - <code>id -g username</code> is simply wrong

# doesn't handle lines which start with whitespace in <tt>/etc/passwd</tt> correctly
# @return <code>True</code> if <tt>username</tt> exists (in <tt>/etc/passwd</tt>)
def check_user_exists(username):
    passwd_lines = file_line_utils.file_lines("/etc/passwd", comment_symbol="#")
    for passwd_line in passwd_lines:
        if passwd_line.startswith(username):
            return True
    return False

# doesn't handle lines which start with whitespace in <tt>/etc/group</tt> correctly
# @return <code>True</code> if <tt>groupname</tt> exists (in <tt>/etc/group</tt>)
def check_group_exists(groupname):
    group_lines = file_line_utils.file_lines("/etc/group", comment_symbol="#")
    for group_line in group_lines:
        if group_line.startswith(groupname):
            return True
    return False

# to be passed to <tt>preexec_fn</tt> argument of relevant subprocess.* functions, e.g. <pre>
# return_code = sp.check_call(["git", "rev-parse"], stderr=sp.PIPE, cwd=base_dir, preexec_fn=user_group_utils.demote_uid(user_group_utils.id_by_username(build_user)))
# </pre>
def demote_uid(uid):
    return demote_uid_gid(uid,uid)

def demote_uid_gid(uid, gid):
    def ret_value():
        os.setgid(gid)
        os.setuid(uid)
    return ret_value

