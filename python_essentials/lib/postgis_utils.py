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

################################################################################
# Authentication 
################################################################################
# As the script provides a host parameter it is necessary to setup 
# authentication for hosts (local connections are setup to be trusted by 
# default) (this is handled with pexpect because this is the way to interact 
# subprocesses querying passwords)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

import subprocess as sp
import os
import time

# different possiblities of installation of postgis and hstore extension on database (extension support is dropped for postgis above 2.x), some package maintainers include scripts nevertheless -> let the caller choose
EXTENSION_INSTALL_EXTENSION = 1 # use the extension command of postgres
EXTENSION_INSTALL_SQL_FILE= 2 # use 
EXTENSION_INSTALLS = [EXTENSION_INSTALL_EXTENSION, EXTENSION_INSTALL_SQL_FILE]
extension_install_default = EXTENSION_INSTALLS[0]

pwfile_path = "./pwfile" # it's not wise to write to a file in system's temporary file directory which is readable for everybody
authmethod = "md5"

postgres_server_start_timeout = 5
postgres_server_stop_timeout = postgres_server_start_timeout

# runs an appropriate initdb routine and initializes md5 login for <tt>db_user</tt>. User <tt>db_user</tt> is created (automatically when <tt>initdb</tt> is invoked with <tt>--username</tt>).
# @args extension_install on of EXTENSION_INSTALLS
# @raise ValueError is extension_install is not one of EXTENSION_INSTALLS
def bootstrap_datadir(datadir_path, db_user, password="somepw", initdb="initdb"):
    pwfile = open(pwfile_path, "w")
    pwfile.write(password)
    pwfile.flush()
    pwfile.close()
    sp.check_call([initdb, "-D", datadir_path, "--username=%s" % db_user, "--pwfile=%s" % pwfile_path, 
        "--auth=%s" % authmethod
    ])
    os.remove(pwfile_path)
    
def __pe_wrapper__(cmds, password):
    psql_proc = pe.spawn(str.join(" ", cmds)) # hstore handled below
    psql_proc.logfile = sys.stdout
    psql_proc.expect(["Password", "Passwort", "postgis"])
    psql_proc.sendline(password)
    psql_proc.wait()

def bootstrap_database(datadir_path, db_port, db_host, db_user, db_name, password="somepw", initdb="initdb", postgres="postgres", createdb="createdb", psql="psql", socket_dir="/tmp", extension_install=extension_install_default):
    if not extension_install in EXTENSION_INSTALLS:
        raise ValueError("extension_install has to be one of %s" % str(EXTENSION_INSTALLS))
    
    # setup hba (could be done in bootstrap_datadir, but this would require 
    # additional arguments)
    pg_hba_conf_file_path = os.path.join(datadir_path, "pg_hba.conf")
    file_utils.append_file(pg_hba_conf_file_path, "\nhost all %s 0.0.0.0 0.0.0.0 %s\n" % (db_user, authmethod))

    postgres_process = sp.Popen([postgres, "-D", datadir_path, "-p", str(db_port), "-h", db_host, "-k", socket_dir])
    try:
        logger.info("sleeping %s s to ensure postgres server started" % postgres_server_start_timeout)
        time.sleep(postgres_server_start_timeout) # not nice (should poll connection until success instead)
        __pe_wrapper__([createdb, "-p", str(db_port), "-h", db_host, "--username=%s" % db_user, db_name], password)

        __pe_wrapper__([psql, "-c", "\"grant all on database %s to %s;\"" % (db_name, db_user), "-p", str(db_port), "-h", db_host, "--username=%s" % db_user], password)
        if extension_install == EXTENSION_INSTALL_EXTENSION:
            __pe_wrapper__([psql, "-d", db_name, "-c", "\"create extension postgis; create extension postgis_topology;\"", "-p", str(db_port), "-h", db_host, "--username=%s" % db_user], password) # hstore handled below
        elif extension_install == EXTENSION_INSTALL_SQL_FILE:
            # ON_ERROR_STOP=1 causes the script to fail after the first failing command which is very useful for debugging as proceed doesn't make sense in a lot of cases
            __pe_wrapper__([psql, "-d", db_name, "-f", "/usr/share/postgresql/%s/contrib/postgis-%s/postgis.sql" % (pg_version, postgis_version_string), "-p", str(db_port), "-h", db_host, "--username=%s" % db_user, "-v", "ON_ERROR_STOP=1"], password)
            __pe_wrapper__([psql, "-d", db_name, "-f", "/usr/share/postgresql/%s/contrib/postgis-%s/topology.sql" % (pg_version, postgis_version_string), "-p", str(db_port), "-h", db_host, "--username=%s" % db_user, "-v", "ON_ERROR_STOP=1"], password)
            __pe_wrapper__([psql, "-d", db_name, "-f", "/usr/share/postgresql/%s/contrib/postgis-%s/spatial_ref_sys.sql" % (pg_version, postgis_version_string), "-p", str(db_port), "-h", db_host, "--username=%s" % db_user, "-v", "ON_ERROR_STOP=1"], password)
        __pe_wrapper__([psql, "-d", db_name, "-c", "\"create extension hstore;\"", "-p", str(db_port), "-h", db_host, "--username=%s" % db_user, "-v", "ON_ERROR_STOP=1"], password) # no sql file for hstore found, so install it from postgresql-contrib-x.x deb package (find another way (check wiki for existing solutions) if trouble occurs)
        __pe_wrapper__([psql, "-c", "\"ALTER USER %s WITH PASSWORD '%s';\"" % (db_user, password), "-p", str(db_port), "-h", db_host, "--username=%s" % db_user], password)
    finally:
        postgres_process.terminate()
        logger.info("sleeping %s s to ensure postgres server stopped" % postgres_server_stop_timeout)
        time.sleep(postgres_server_stop_timeout)

