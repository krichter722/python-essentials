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

import pm_utils

skip_apt_update_default = False

def mount_prerequisites(skip_apt_update=skip_apt_update_default):
    """Checks whether necessary packages for mounting have been installed and installs them if necessary using `pm_utils.install_packages`. Returns `True` if packages were installed and `False`otherwise."""
    installed = False
    if not pm_utils.dpkg_check_package_installed("nfs-common"):
        pm_utils.install_packages(["nfs-common"], skip_apt_update=skip_apt_update)
        installed = True
    if not pm_utils.dpkg_check_package_installed("cifs-utils"):
        pm_utils.install_packages(["cifs-utils"], skip_apt_update=skip_apt_update)
        installed = True
    return installed

