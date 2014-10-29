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
#    
#    The retrieve_hash function code was authored by stack exchange user 
#    omnifarious (http://stackoverflow.com/users/167958/omnifarious) on 
#    stackoverflow.com

import os
import shutil
import subprocess as sp
import logging
import re
import hashlib

logger = logging.getLogger("file_utils")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# choose backup postfix from a sequence of numbers
BACKUP_TYPE_SEQUENCE = 1
# choose the SHA1 sum of the file to be backed up and skip existing backups based on the file name
BACKUP_TYPE_SHA1 = 2
BACKUP_TYPE_NONE = 3 # should be a digit in order to make it parsable from command line (when the setup is enforced with a positional parameter)
backup_type_default= BACKUP_TYPE_SEQUENCE
backup_types = [BACKUP_TYPE_SEQUENCE, BACKUP_TYPE_SHA1, BACKUP_TYPE_NONE]

################################################################################
# link tools                                                                   #
################################################################################

# If <tt>link_name</tt> doesn't exist, creates link to <tt>point_to</tt> named <tt>link_name</tt>, otherwise checks 
# 1.) if existing <tt>link_name</tt> is a link and points already to <tt>point_to</tt>
# 2.) or a link pointing to another location than point_to
# and skips if 1. is the case and overwrites <tt>link_name</tt> if 2. is the case. Creates a backup of overwritten files or links if <tt>backup</tt> is <code>True</code>.
# @args backup creates a backup in the form filename.bk<N> where N is the minimal number denoting a filesname which doesn't exist. Backup is not created if the content of <tt>point_to</tt> and <tt>link_name</tt> are identical. If <tt>link_name</tt> is a link, the link target is backed up (because backing up the link doesn't make sense).
# @return <code>False</code> if the link could not be created due to existance of the <tt>link_name</tt> (and <tt>force</tt> being <code>False</code>).
def checked_link(point_to, link_name, force=False, backup_type=backup_type_default):
    if not backup_type in backup_types:
        raise ValueError("backup_type '%s' isn't one of %s" % (backup_type,backup_types))
    target_parent = os.path.abspath(os.path.join(link_name, '..'))
    if not os.path.lexists(target_parent):
        os.makedirs(target_parent)
    if not os.path.lexists(link_name):
        os.symlink(point_to,link_name)
        return True
    else:
        if not force:
            return False
    if os.path.islink(link_name) and os.path.realpath(link_name) == point_to:
        return True
    if os.path.exists(link_name):
        if backup_type != BACKUP_TYPE_NONE:
            backup_file(link_name, backup_type=backup_type)
        else:
            if not os.path.isdir(link_name) or os.path.islink(link_name):
                os.remove(link_name)
            else:
                shutil.rmtree(link_name)
    os.symlink(point_to, link_name)
    return True
# implementation notes:
# - skipping backup if file content are identical is not useful because if was initially intended to avoid endless identical backups of links which now handled smarter by skipping link creation when link exists and points to the source already

################################################################################
# Write tools                                                                  #
################################################################################

def write_file(file0, what):
    if os.path.isdir(file0):
        raise ValueError("file %s is a directory" % file0)
    if lazy_newline and not what.endswith("\n"):
        what = "%s\n" % what
    file_obj = open(file0, 'w')
    file_obj.write(what)
    file_obj.flush()
    file_obj.close()

# appends <tt>what</tt> to file with path <tt>file0</tt>. Creates file if it doesn't exist. Newline character is appended if <tt>lazy_newline</tt> is <code>True</code> and <tt>what</tt> doesn't end with a newline yet.
# raises <tt>ValueError</tt> if <tt>file0</tt> is a directory
def append_file(file0, what, lazy_newline=True):
    if os.path.isdir(file0):
        raise ValueError("file %s is a directory" % file0)
    if lazy_newline and not what.endswith("\n"):
        what = "%s\n" % what
    file_obj = open(file0, 'a')
    file_obj.write(what)
    file_obj.flush()
    file_obj.close()

def check_dir(dir_path):
    if not os.path.exists(dir_path):
        return False
    if not os.path.isdir(dir_path):
        raise ValueError("dir_path has to point to a directory")
    if len(os.listdir(dir_path)) == 0:
        logger.debug("%s is empty" % dir_path)
        return False
    return True

def create_dir(dir_path, allow_content):
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            if len(os.listdir(dir_path)) > 0 and not allow_content:
                raise RuntimeError("%s exists and has content, a directory is supposed to be created. Remove or move the content of the directory" % dir_path)
        else:
            # file
            raise RuntimeError("%s exists, a directory is supposed to be created. Remove or move the file" % dir_path)
    else:
        os.makedirs(dir_path)

def check_file(file_path, md5sum):
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        raise ValueError("file_path has to point to a file")
    retrieved_md5sum = retrieve_hash(file_path)
    if not retrieved_md5sum == md5sum:
        logger.debug("%s has md5 sum %s instead of %s" % (file_path, retrieved_md5sum, md5sum))
        return False
    return True

def retrieve_hash(file_path, hasher="md5", blocksize=65536):
    afile = open(file_path, "r")
    hasher_instance = hashlib.new(hasher)
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher_instance.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    ret_value = hasher_instance.hexdigest()
    return ret_value

# @return the XOR of all file content, name and directory name hashes in order 
# to track any changes (even one simple rename of a file or directory)
def retrieve_hash_recursive(dir_path, hasher="md5", blocksize=65536):
    logger.debug("generating recursive hash for '%s'" % (dir_path,))
    if not os.path.isdir(dir_path):
        raise ValueError("dir_path '%s' isn't a directory" % (dir_path,))
    ret_value = 0
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for filename in filenames:
            current_file_path = os.path.join(dirpath, filename)
            hasher_instance = hashlib.new(hasher)
            hasher_instance.update(current_file_path)
            ret_value = ret_value ^ int(hasher_instance.hexdigest(), base=16)
            ret_value = ret_value ^ int(retrieve_hash(current_file_path, hasher=hasher, blocksize=65536), base=16)
        for dirname in dirnames:
            current_dir_path = os.path.join(dirpath, dirname)
            hasher_instance = hashlib.new(hasher)
            hasher_instance.update(current_dir_path)
            ret_value = ret_value ^ int(hasher_instance.hexdigest(), base=16)
    return str(ret_value)

# moves the file to a backup location (i.e. file_path no longer exists after 
# the function run)
# @args file_path a path of an existing file or directory
def backup_file(file_path, backup_type=backup_type_default, follow_links=False):
    if not os.path.exists(file_path):
        raise ValueError("file_path '%s' doesn't exist, backup_file only accepts an existing file or directory as argument" % (file_path,))
    if backup_type == BACKUP_TYPE_SHA1:
        if os.path.isdir(file_path):
            file_sha1 = retrieve_hash_recursive(file_path, hasher="sha1")
        else:
            file_sha1 = retrieve_hash(file_path, hasher="sha1")
        file_backup_path = "%s.bk-%s" % (file_path, file_sha1)
        if not os.path.exists(file_backup_path):
            os.rename(os.path.realpath(file_path), file_backup_path)
    elif backup_type == BACKUP_TYPE_SEQUENCE:
        renamepostfix = ".bk"
        renamepostfixcount = 0
        backup_file = file_path
        if follow_links:
            backup_file = os.path.realpath(file_path)
        if os.path.lexists(backup_file):
            renamepostfix = ".bk%d" % renamepostfixcount
            renamepostfixcount += 1
        while os.path.lexists(backup_file+renamepostfix):
            renamepostfix = ".bk%d" % renamepostfixcount
            renamepostfixcount += 1
        target_backup_path = backup_file+renamepostfix
        logger.debug("backing up %s to %s" % (backup_file, target_backup_path))
        os.rename(backup_file, target_backup_path)
    else:
         raise ValueError("backup_type '%s' isn't supported" % (backup_type,))
