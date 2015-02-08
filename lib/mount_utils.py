#!/usr/bin/python
# coding: utf-8

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

import argparse
import subprocess as sp
import os
import sys
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

import file_line_utils

# binaries
mount_default = "mount"
bash = "dash"
ifconfig = "ifconfig"
losetup = "losetup"
partprobe = "partprobe"
btrfs = "btrfs"
umount = "umount"

IMAGE_MODE_PT="partition-table"
IMAGE_MODE_FS="file-system"
image_modes = [IMAGE_MODE_PT, IMAGE_MODE_FS]

MOUNT_MODE_NFS = 1
MOUNT_MODE_CIFS = 2
mount_mode_default = MOUNT_MODE_CIFS

def mount_dsm_sparse_file(shared_folder_name, image_mount_target, network_mount_target, image_file_name, remote_host, username, uid=1000, gid=1000, mount_mode=mount_mode_default, credentials_file=None, mount=mount_default):
    """a wrapper around `mount_sparse_file` and different remote mount methods (NFS, cifs, etc.) (sparse file support is horrible for all of them...). It has been written to deal with Synology DSM 5.0 (path specifications, etc.). `credentials_file` can be used of the `credentials` option of `mount.cifs` will be passed to the `mount` command, if `None` the `username` option with value will be passed to the `mount` command which will request the password from input at a prompt. `uid` and `gid` are values for options of `mount.cifs` (which default to Ubuntu defaults for the first user)."""
    if mount_mode == MOUNT_MODE_NFS:
        lazy_mount(source="%s:/volume1/%s" % (remote_host, shared_folder_name), target=network_mount_target, fs_type="nfs", options_str="nfsvers=4", mount=mount) 
                # handles inexistant target
                # omitting nfsvers=4 causes 'mount.nfs: requested NFS version or transport protocol is not supported' (not clear with which protocol this non-sense error message refers to)
    elif mount_mode == MOUNT_MODE_CIFS:
        if credentials_file is None:
            options_str="username=%s,rw,uid=%d,gid=%d" % (username, uid, gid, )
        else:
            if not os.path.exists(credentials_file):
                raise ValueError("credentials_file '%s' doesn't exist" % (credentials_file,))
            options_str="credentials=%s,rw,uid=%d,gid=%d" % (credentials_file, uid, gid, )
        lazy_mount(source="//%s/%s" % (remote_host, shared_folder_name), target=network_mount_target, fs_type="cifs", options_str=options_str, mount=mount) # handles inexistant target
    else:
        raise ValueError("mount_mode '%s' not supported" % (mount_mode,))
    mount_sparse_file(
        image_file=os.path.join(network_mount_target, image_file_name), 
        image_mount_target=image_mount_target, 
        image_mode=IMAGE_MODE_FS,
        mount=mount
    )

def mount_sparse_file(image_file, image_mount_target, image_mode=IMAGE_MODE_FS, mount=mount_default):
    """Handles mounting `image_file` at `image_mount_target` according to `image_mode` which determines the remote filesystem to use."""
    image_file_loop_dev = losetup_wrapper(image_file)
    if image_mode == IMAGE_MODE_PT:
        sp.check_call([partprobe, image_file_loop_dev])
        lazy_mount("%sp1" % image_file_loop_dev, image_mount_target, "btrfs", mount=mount)
        sp.check_call([btrfs, "device", "scan", "%sp1" % image_file_loop_dev]) # scan fails if an image with a partition table is mounted at the loop device -> scan partitions 
    elif image_mode == IMAGE_MODE_FS:
        lazy_mount(image_file_loop_dev, image_mount_target, "btrfs", mount=mount)
        sp.check_call([btrfs, "device", "scan", image_file_loop_dev]) # do this always as it doesn't fail if not btrfs image 
        # has been mounted and doesn't take a lot of time -> no need to add 
        # a parameter to distungish between btrfs and others (would be more 
        # elegant though)
    else:
        raise ValueError("image_mode has to be one of %s, but is %s" % (str(image_modes), image_mode))

def unmount_sparse_file(mount_target):
    """Unmounts the parse file which has been mounted under `mount_target` and removes the association of that sparse file with its loop device. The loop device will be determined automatically based on `losetup`."""
    mount_source = get_mount_source(mount_target)
    if mount_source is None:
        raise ValueError("mount_target '%s' isn't using a loop device" % (mount_target,))
    logger.info("mount_target '%s' was using loop device '%s'" % (mount_target, mount_source))
    sp.check_call([umount, mount_target])
    sp.check_call([losetup, "-d", mount_source])

def get_mount_source(mount_target):
    """Determines the directory or filesystem which is mounted under `mount_target` and returns it or `None` is no directory of filesystem is mounted under `mount_target`."""
    for mount_source, mount_target0 in [tuple(re.split("[\\s]+", x)[0:2]) for x in file_line_utils.file_lines("/proc/mounts", comment_symbol="#")]:
        if mount_target0 == mount_target:
            return mount_source
    return None

def losetup_wrapper(file):
    """A wrapper around finding the next free loop device with `losetup` and associating `file` with it with one function call. Returns the found loop device `file` has been associated to."""
    try:
        loop_dev = sp.check_output([losetup, "-f"]).decode("utf-8").strip()
    except sp.CalledProcessError as ex:
        raise RuntimeError("no free loop device")
    sp.check_call([losetup, loop_dev, file])
    return loop_dev

def check_mounted(source, target, mount=mount_default):
    """Checks whether `source` is mounted under `target` and `True` if and only if that's the case - and `False` otherwise."""
    mount_lines = sp.check_output([mount]).decode("utf-8").strip().split("\n") # open("/proc/mounts", "r").readlines() is not compatible with FreeBSD
    for mount_line in mount_lines:
        mount_line_split = mount_line.split(" ")
        target0 = mount_line_split[1]
        if target0 == target: # don't check equality of source with (1st column of) mount output because multiple usage of mount target isn't possible and therefore the check should already succeed if the mount target is used by a (possibly other) mount source
            return True
    return False

def lazy_mount(source, target, fs_type, options_str=None, mount=mount_default):
    """Checks if `source` is already mounted under `target` and skips (if it is) or mounts `source` under `target` otherwise as type `fs_type`. Due to the fact that the type can be omitted for certain invokations of `mount` (e.g. `mount --bind`), this function allows `fs_type` to be `None` which means no type will be specified. Uses `mount` as binary for the mount command."""
    if check_mounted(source, target, mount=mount):
        return
    if not os.path.lexists(target):
        if os.path.isfile(source):
            os.mknod(target, mode=0o0755)
        else:
            os.makedirs(target)
    cmds = [mount]
    if fs_type != None and fs_type != "":
    	cmds += ["-t", fs_type,]
    if not options_str is None and options_str != "":
        cmds += ["-o", options_str]
    cmds += [ source, target]
    sp.check_call(cmds)
