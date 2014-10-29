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

import logging
logger = logging.getLogger("pm_utils")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

import subprocess
import os
import sys
import tempfile
import re
import check_os
import string
import augeas

# indicates whether apt is up to date, i.e. whether `apt-get update` has been invoked already
aptuptodate = False
# indicates that apt sources are invalid, e.g. after packages sources have been changed @TODO: explain why in comment here
apt_invalid = False
dpkglock = "/var/lib/dpkg/lock"
apt_get= "apt-get"
add_apt_repository = "add-apt-repository"

assume_yes_default = False
skip_apt_update_default = False

##############################
# dpkg tools
##############################
# @return <code>True</code> if <tt>package_name</tt> is installed, <code>False</code> otherwise
def dpkg_check_package_installed(package_name):
    return_code = subprocess.call(["dpkg", "-s", package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return return_code == 0

##############################
# apt-get tools
##############################
# a wrapper around <tt>apt-get dist-upgrade</tt> to use the internal aptuptodate flag
def apt_get_dist_upgrade(skip_apt_update=skip_apt_update_default):
    if not skip_apt_update:
        aptupdate()
    subprocess.check_call([apt_get, "dist-upgrade"])

def install_apt_get_build_dep(packages, package_manager="apt-get", assume_yes=assume_yes_default, skip_apt_update=skip_apt_update_default):
    if packages == None or not type(packages) == type([]):
        raise Exception("packages has to be not None and a list")
    if len(packages) == 0:
        return 0
    if not skip_apt_update:
        aptupdate()
    for package in packages:
        apt_get_output = subprocess.check_output([apt_get, "--dry-run", "build-dep", package]).strip().decode("utf-8")
        apt_get_output_lines = apt_get_output.split("\n")
        build_dep_packages = []
        for apt_get_output_line in apt_get_output_lines:
            if apt_get_output_line.startswith("  "):
                build_dep_packages += re.split("[\\s]+", apt_get_output_line)
        install_packages(build_dep_packages, package_manager, assume_yes, skip_apt_update=skip_apt_update) 
        
# @return <code>True</code> if all packages in <tt>packages</tt> are installed via <tt>package_manager</tt>, <code>False</code> otherwise
def check_packages_installed(packages, package_manager="apt-get", skip_apt_update=skip_apt_update_default):
    package_managers = ["apt-get"]
    if package_manager == "apt-get":
        #try:
        #    import apt
        #    import apt_pkg
        #except ImportError:
        #    print("installing missing apt python library")
        #    install_apt_python()
        #apt_pkg.init()
        #cache = apt.Cache()
        for package in packages:
            package_installed = dpkg_check_package_installed(package)
            if not package_installed:
                return False            
            #found = False
            #for cache_entry in cache:
            #    if cache_entry.name == package:
            #        found = True
            #        if not cache_entry.is_installed: # cache_entry.isInstalled in version ?? before ??
            #            cache.close()
            #            return False
            #        break
            #if not found:
            #    cache.close()
            #    return False
        #cache.close()
        return True
    else:
        raise Exception("package_manager has to be one of "+str(package_managers))

# quiet flag doesn't make sense because update can't be performed quietly obviously (maybe consider to switch to apt-api)
# return apt-get return code or <code>0</code> if <tt>packages</tt> are already installed or <tt>packages</tt> is empty
def install_packages(packages, package_manager="apt-get", assume_yes=assume_yes_default, skip_apt_update=skip_apt_update_default):
    if check_packages_installed(packages, package_manager, skip_apt_update=skip_apt_update):
        return 0
    return __package_manager_action__(packages, package_manager, ["install"], assume_yes, skip_apt_update=skip_apt_update)

# doesn't check whether packages are installed
# @return apt-get return code or <code>0</code> if <tt>packages</tt> is empty
def reinstall_packages(packages, package_manager="apt-get", assume_yes=assume_yes_default, skip_apt_update=skip_apt_update_default, stdout=None):
    return __package_manager_action__(packages, package_manager, ["--reinstall", "install"], assume_yes, skip_apt_update=skip_apt_update,stdout=None)

# @return apt-get return code oder <code>0</code> if none in <tt>packages</tt> is installed or <tt>packages</tt> is empty
def remove_packages(packages, package_manager="apt-get", assume_yes=assume_yes_default, skip_apt_update=skip_apt_update_default):
    return __package_manager_action__(packages, package_manager, ["remove"], assume_yes, skip_apt_update=skip_apt_update)

# quiet flag doesn't make sense because update can't be performed quietly obviously (maybe consider to switch to apt-api)
# @args a list of command to be inserted after the package manager command and default options and before the package list
def __package_manager_action__(packages, package_manager, package_manager_action, assumeyes, skip_apt_update=skip_apt_update_default, stdout=None):
    if not "<type 'list'>" == str(type(packages)):
        raise ValueError("packages isn't a list")
    if len(packages) == 0:
        return 0
    assumeyescommand = ""
    if assumeyes:
        assumeyescommand = "--assume-yes"
    if package_manager == "apt-get":
        packagestring = string.join(packages, " ")
        if not skip_apt_update:
            aptupdate()
        command_list = [apt_get, "--no-install-recommends"]
        if assumeyes:
            command_list.append("--assume-yes")
        try:
            subprocess.check_call(command_list+package_manager_action+packages)
        except subprocess.CalledProcessError as ex:
            raise ex
    elif package_manager == "yast2":
        subprocess.check_call(["/sbin/yast2", "--"+package_manager_action]+packages) # yast2 doesn't accept string concatenation of packages with blank, but the passed list (it's acutually better style...)
    elif package_manager == "zypper":
        subprocess.check_call(["zypper", package_manager_action, packagestring])
    elif package_manager == "equo":
        subprocess.check_call(["equo", package_manager_action, packagestring])
    else:
        raise ValueError(str(package_manager)+" is not a supported package manager")
# implementation notes:
# - changed from return value to void because exceptions can be catched more elegant with subprocess.check_call
# - not a good idea to redirect output of subcommand other than update to file because interaction (e.g. choosing default display manager, comparing config file versions) is useful and necessary and suppressed when redirecting to file
# - checking availability of apt lock programmatically causes incompatibility with invokation without root privileges -> removed

# updates apt using apt-get update command. Throws exceptions as specified by subprocess.check_call if the command fails
def invalidate_apt():
    global apt_invalid
    apt_invalid = True
    global aptuptodate
    aptuptodate = False

# updates apt using subprocess.check_call, i.e. caller has to take care to handle exceptions which happen during execution
def aptupdate(force=False):
    global aptuptodate
    if not aptuptodate or force or apt_invalid:
        print("updating apt sources")
        try:
            apt_get_update_log_file_tuple = tempfile.mkstemp("libinstall_apt_get_update.log")
            logger.info ("logging output of apt-get update to %s" % apt_get_update_log_file_tuple[1])
            subprocess.check_call([apt_get, "--quiet", "update"], stdout=apt_get_update_log_file_tuple[0])
        except subprocess.CalledProcessError as ex:
            raise ex       
        aptuptodate = True

################################################################################
# apt source entries                                                           #
################################################################################
valid_source_line_types = ["deb", "deb-src"]

def __validate_apt_source_function_params_augeas_root__(augeas_root, sources_dir_path, sources_file_path):
    if augeas_root is None:
        raise ValueError("augeas_root mustn't be None")
    if not os.path.exists(augeas_root):
        raise ValueError("augeas_root '%s' doesn't exist" % (augeas_root,))
    if not os.path.isdir(augeas_root):
        raise ValueError("augeas_root '%s' isn't a directory, but has to be" % 
(augeas_root))
    if not os.path.exists(sources_dir_path):
        raise ValueError("sources_dir_path '%s' doesn't exist" % 
(sources_dir_path,))
    if not os.path.exists(sources_file_path):
        raise ValueError("sources_file_path '%s' doesn't exist" % 
(sources_file_path,))

def __validate_apt_source_function_params_type__(the_type):
    if not the_type in valid_source_line_types:
        raise ValueError("the_type '%s' isn't a valid source line type (has to be one of %s)" % (the_type, valid_source_line_types))

# Avoids the weakness of <tt>add-apt-repository</tt> command to add commented duplicates of lines which are already present by not adding those at all.
# @args uri the URI of the apt line
# @args component the component to be served (e.g. main)
# @args distribution the distribution of the entry (e.g. trusty for an Ubuntu 14.04 system)
# @args the_type the type of the entry (usually <tt>deb</tt> or <tt>deb-src</tt>)
def check_apt_source_line_added(uri, component, distribution, the_type, augeas_root="/",):
    sources_dir_path= os.path.join(augeas_root, "etc/apt/sources.list.d")
    sources_file_path= os.path.join(augeas_root, "etc/apt/sources.list")
    __validate_apt_source_function_params_augeas_root__(augeas_root, sources_dir_path, sources_file_path)
    __validate_apt_source_function_params_type__(the_type)
    
    a = augeas.Augeas(root=augeas_root)
    # workaround missing loop label feature with inner function
    def __search__():
        for sources_dir_file in [os.path.join(sources_dir_path, x) for x in os.listdir(sources_dir_path)]:
            commented_in_lines = a.match("/files/%s/*" % (os.path.relpath(sources_dir_file,augeas_root),)) # match doesn't return lines with comments; it doesn't matter whether ppa_sources_d_file starts with / for the match statement
            for commented_in_line in commented_in_lines:
                if a.get("%s/uri" % (commented_in_line,)) == uri and a.get("%s/component" % (commented_in_line,)) == component and a.get("%s/distribution" % (commented_in_line,)) == distribution and a.get("%s/type" % (commented_in_line,)) == the_type:
                    return True
        return False
    match_found = __search__()
    if match_found:
        return True
    if not match_found:
        # only search in source.list if not found because there's no need to do 
        # any validation in this this function
        commented_in_lines = a.match("/files/%s/*" % (os.path.relpath(sources_file_path,augeas_root),)) # match doesn't return lines with comments; it doesn't matter whether ppa_sources_d_file starts with / for the match statement
        match_found = False
        for commented_in_line in commented_in_lines:
            if a.get("%s/uri" % (commented_in_line,)) == uri and a.get("%s/component" % (commented_in_line,)) == component and a.get("%s/distribution" % (commented_in_line,)) == distribution and a.get("%s/type" % (commented_in_line,)) == the_type:
                a.close()
                return True
    a.close()
    return False

# adds an entry based on <tt>uri</tt>, <tt>component</tt>, 
# <tt>distribution</tt> and <tt>the_type</tt> to <tt>etc/apt/sources.list</tt> 
# relatively to <tt>augeas_root</tt>.
# 
# Consider using add-apt-repository or manually adding an entry in a separate 
# file into <tt>/etc/apt/sources.d/</tt>.
# 
# There's no validation of parameters except <tt>augeas_root</tt>, i.e. this 
# might mess up your <tt>sources.list</tt> file quite easily.
def add_apt_source_line(uri, component, distribution, the_type, augeas_root="/",):
    sources_dir_path= os.path.join(augeas_root, "etc/apt/sources.list.d")
    sources_file_path= os.path.join(augeas_root, "etc/apt/sources.list")
    __validate_apt_source_function_params_augeas_root__(augeas_root, sources_dir_path, sources_file_path)
    __validate_apt_source_function_params_type__(the_type)
    
    a = augeas.Augeas(root=augeas_root)
    a.set("/files/etc/apt/sources.list/01/distribution", distribution) # checkout http://augeas.net/tour.html if you find the 01 label for adding entries confusing (it simply is...)
    a.set("/files/etc/apt/sources.list/01/type", the_type)
    a.set("/files/etc/apt/sources.list/01/uri", uri)
    a.set("/files/etc/apt/sources.list/01/component", component)
    a.save()
    a.close()
