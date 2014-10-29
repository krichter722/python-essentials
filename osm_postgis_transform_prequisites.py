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

import sys
import os
import pm_utils
import check_os
import postgis_utils
import os_utils
import subprocess as sp
import string
import plac

postgis_src_dir_name="postgis-2.1.1"
postgis_url_default = "http://download.osgeo.org/postgis/source/postgis-2.1.1.tar.gz"
postgis_src_archive_name = "postgis-2.1.1.tar.gz"
postgis_src_archive_md5 = "4af86a39e2e9dbf10fe894e03c2c7027"
postgis_jdbc_name = "postgis-jdbc-2.1.0SVN.jar"

@plac.annotations(
    skip_database_installation=("whether to skip installation ofpostgresql and postgis related prequisites", "flag"),
    skip_apt_update=("whether (possibly time consuming) invokation of apt-get update ought to be skipped (if have reason to be sure that your apt sources are quite up-to-date, e.g. if you invoked apt-get 5 minutes ago", "flag"),
    postgis_url=("The URL where the postgis tarball ought to be retrieved", "option")
)
def install_prequisites(skip_database_installation, skip_apt_update, postgis_url=postgis_url_default,):
    if check_os.check_ubuntu() or check_os.check_debian():
        if skip_database_installation:
            pm_utils.install_packages(["osm2pgsql"], package_manager="apt-get", skip_apt_update=skip_apt_update, assume_yes=False)
        else:
            release_tuple = check_os.findout_release_ubuntu_tuple()
            install_postgresql(skip_apt_update=skip_apt_update)
    else:
        if skip_database_installation:
            raise RuntimeError("implement simple installation of only prequisite osm2pgsql")
        else:
            install_postgresql(skip_apt_update=skip_apt_update)

def install_postgresql(skip_apt_update, pg_version=(9,2),):
    if check_os.check_ubuntu() or check_os.check_debian() or check_os.check_linuxmint():
        # only add apt source for ubuntu and debian and fail in linuxmint if 
        # release is < 17 where the packages are available
        if check_os.check_ubuntu() or check_os.check_debian():
            if check_os.check_ubuntu():   
                release_tuple = check_os.findout_release_ubuntu_tuple()
                if release_tuple > (12,4) and release_tuple < (13,10):
                    release = "precise" # repository provides for precise, saucy and trusty
                else:
                    release = check_os.findout_release_ubuntu()
            elif check_os.check_debian():
                release = check_os.findout_release_debian()
            else:
                raise RuntimeError("operating system not supported")
            apt_url = "http://apt.postgresql.org/pub/repos/apt/"
            distribution = "%s-pgdg" % release
            component = "main"
            if not pm_utils.check_apt_source_line_added(uri=apt_url, component=component, distribution=distribution, the_type="deb", augeas_root="/",):
                postgresql_sources_file_path = "/etc/apt/sources.list.d/postgresql.list"
                logger.info("adding postgresql apt source file '%s'" % (postgresql_sources_file_path,))
                postgresql_sources_file = open(postgresql_sources_file_path, "w")
                postgresql_sources_file.write("deb %s %s %s" % (apt_url, distribution, component, ))
                postgresql_sources_file.flush()
                postgresql_sources_file.close()
                os.system("wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -")
                pm_utils.invalidate_apt()
        else:
            # linuxmint
            release = check_os.findout_release_linuxmint()
            if release < 17:
                raise RuntimeError("linuxmint releases < 17 aren't supported")
        pg_version_string = string.join([str(x) for x in pg_version],".")
        try:
            pm_utils.install_packages([ 
                "postgresql-%s" % pg_version_string, 
                "postgresql-%s-postgis-2.1" % pg_version_string, 
                "postgresql-%s-postgis-2.1-scripts" % pg_version_string,
                "postgresql-contrib-%s" % pg_version_string, 
                "postgresql-client-common", # version independent, no package per version
            ], package_manager="apt-get", skip_apt_update=skip_apt_update)
        except sp.CalledProcessError as ex:
            print("postgresql installation failed (which might be caused by breakage of apt package in Ubuntu 13.10")
            #pm_utils.remove_packages(["postgresql", "postgresql-common"], package_manager="apt-get", skip_apt_update=skip_apt_update) 
            #postgresql_deb_path = os.path.join(tmp_dir, postgresql_deb_name)
            #if not check_file(postgresql_deb_path, postgresql_deb_md5):
            #    do_wget(postgresql_deb_url, postgresql_deb_path)
            #    sp.check_call([dpkg, "-i", postgresql_deb_path])
            psql = "/opt/postgres/%s/bin/psql" % pg_version_string
            initdb = "/opt/postgres/%s/bin/initdb" % pg_version_string
            createdb = "/opt/postgres/%s/bin/createdb" % pg_version_string
            postgres = "/opt/postgres/%s/bin/postgres" % pg_version_string
        # osmpgsql
        pm_utils.install_packages(["osm2pgsql"], package_manager="apt-get", skip_apt_update=skip_apt_update)
    elif check_os.check_opensuse():
        if pg_version == (9,2):
            sp.check_call([zypper, "install", "postgresql", "postgresql-contrib", "postgresql-devel", "postgresql-server"])
            psql = "/usr/lib/postgresql92/bin/psql"
            initdb = "/usr/lib/postgresql92/bin/initdb" 
            createdb = "/usr/lib/postgresql92/bin/createdb"
            postgres = "/usr/lib/postgresql92/bin/postgres"
        else:
            # better to let the script fail here than to get some less comprehensive error message later
            raise RuntimeError("postgresql version %s not supported" % string.join([str(x) for x in pg_version],"."))
    else:
        # better to let the script fail here than to get some less comprehensive error message later
        raise RuntimeError("operating system not supported!")

if __name__ == "__main__":
    plac.call(install_prequisites)

