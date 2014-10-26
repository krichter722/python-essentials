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

# internal implementation notes:
# - @TODO: handle i18n for pexpect

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

import subprocess as sp
import os
import time
import string
import argparse
import sys
sys.path.append(os.path.realpath(os.path.join(__file__, "..", 'lib')))
import pm_utils
import check_os
import postgis_utils
import os_utils
import pexpect

pg_version = "9.2"
postgis_version = (2,0)
postgis_version_string = string.join([str(i) for i in postgis_version],".")
initdb = "/usr/lib/postgresql/%s/bin/initdb" % pg_version
postgres = "/usr/lib/postgresql/%s/bin/postgres" % pg_version
psql = "/usr/lib/postgresql/%s/bin/psql" % pg_version
createdb = "/usr/lib/postgresql/%s/bin/createdb" % pg_version
osm2pgsql_number_processes = int(sp.check_output(["grep", "-c", "^processor", "/proc/cpuinfo"]).strip())
db_socket_dir = "/tmp"
unprivileged_uid = 1000

start_db_default = False
start_db_option = "t"
start_db_option_long = "start-db"
db_host_default = "localhost"
db_host_option = "j"
db_host_option_long = "host"
db_port_default = 5204
db_port_option = "p"
db_port_option_long = "port"
db_user_default = "postgis"
db_user_option = "u"
db_user_option_long = "user"
db_password_default = "postgis"
db_password_option = "w"
db_password_option_long = "password"
db_name_default = "postgis"
db_name_option = "n"
db_name_option_long = "database-name"
osm2pgsql_default = "osm2pgsql"
osm2pgsql_option = "q"
osm2pgsql_option_long = "osm2pgsql"

data_dir_default = "/mnt/osm_postgis/postgis-%s" % pg_version
data_dir_option = "d"
data_dir_option_long = "data-dir"

osm_files_option = "o"
osm_files_option_long = "osm-files"

cache_size_default=1000
cache_size_option = "c"
cache_size_option_long = "cache-size"

# the time the scripts (main thread) waits for the postgres server to be available and accepting connections
postgres_server_start_timeout = 5

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("-%s" % data_dir_option, "--%s" % data_dir_option_long, type=str, nargs='?',
                   help='', dest=data_dir_option_long, required=True)
parser.add_argument("-%s" % osm_files_option, "--%s" % osm_files_option_long, type=str, nargs='+',
                   help='list of OSM files to be passed to osm2pgsql', dest=osm_files_option_long, required=True)
parser.add_argument("-%s" % cache_size_option, "--%s" % cache_size_option_long, type=int, nargs='?', default=cache_size_default, 
                   help='size of osm2pgsql cache', dest=cache_size_option_long)
parser.add_argument("-%s" % start_db_option, "--%s" % start_db_option_long, default=start_db_default, type=bool, nargs='?',
                   help='whether to start an postgres process as a child of the script process  (using the following arguments) or to connect to an already running process (using the following arguments)', dest=start_db_option_long)
parser.add_argument("-%s" % db_host_option, "--%s" % db_host_option_long, default=db_host_default, type=str, nargs='?',
                   help='host where the database ought to be available for further connections (if -%s (--%s) is True) or the host where to reach the already running postgres process (if -%s (--%s) is False)' % (start_db_option, start_db_option_long, start_db_option, start_db_option_long), dest=db_host_option_long)
parser.add_argument("-%s" % db_port_option, "--%s" % db_port_option_long, default=db_port_default, type=int, nargs='?',
                   help='@TODO', dest=db_port_option_long)
parser.add_argument("-%s" % db_user_option, "--%s" % db_user_option_long, default=db_user_default, type=str, nargs='?',
                   help='@TODO', dest=db_user_option_long)
parser.add_argument("-%s" % db_password_option, "--%s" % db_password_option_long, default=db_password_default, type=str, nargs='?',
                   help='@TODO', dest=db_password_option_long)
parser.add_argument("-%s" % db_name_option, "--%s" % db_name_option_long, default=db_name_default, type=str, nargs='?',
                   help='@TODO', dest=db_name_option_long)
parser.add_argument("-%s" % osm2pgsql_option, "--%s" % osm2pgsql_option_long, default=osm2pgsql_default, type=str, nargs='?',
                   help='path to the osm2pgsql binary', dest=osm2pgsql_option_long)

# fails by default because osm_files mustn't be empty
# @args db_user when <tt>start_db</tt> is <code>True</code> used as superuser name, otherwise user to connect as to the database denotes by <tt>db_*</tt> parameter of this function
def osm_postgis_transform(data_dir=data_dir_default, osm_files=[], cache_size=cache_size_default, start_db=start_db_default, db_host=db_host_default, db_port=db_port_default, db_user=db_user_default, db_password=db_password_default, db_name=db_name_default, osm2pgsql=osm2pgsql_default):
    if osm_files is None:
        raise ValueError("osm_files mustn't be None")
    if str(type(osm_files)) != "<type 'list'>":
        raise ValueError("osm_files has to be a list")
    if len(osm_files) == 0:
        raise ValueError("osm_files mustn't be empty")
    if pg_version == "9.2":
        if postgis_version > (2,0):
            raise ValueError("postgis > %s is not compatible with postgresql %s" % (postgis_version_string, pg_version))
    
    # always check, even after install_prequisites
    #@TODO: not sufficient to binary name; necessary to evaluate absolute path with respect to $PATH
    if os_utils.which(osm2pgsql) is None:
        raise RuntimeError("osm2pgsql not found, make sure you have invoked osm_postgis_transform_prequisites.py")
    
    # parsing
    # postgres binary refuses to run when process uid and effective uid are not identical    
    postgres_proc = None
    try:
        if start_db:
            if not os.path.exists(data_dir) or len(os.listdir(data_dir)) == 0:
                postgis_utils.bootstrap_datadir(data_dir, db_user, password=db_password, initdb=initdb)
                postgis_utils.bootstrap_database(data_dir, db_port, db_host, db_user, db_name, password=db_password, initdb=initdb, postgres=postgres, createdb=createdb, psql=psql, socket_dir=db_socket_dir)
            if postgres_proc is None:
                postgres_proc = pexpect.spawn(str.join(" ", [postgres, "-D", data_dir, "-p", str(db_port), "-h", db_host, "-k", db_socket_dir]))
                postgres_proc.logfile = sys.stdout
                logger.info("sleeping %s s to ensure postgres server started" % postgres_server_start_timeout)
                time.sleep(postgres_server_start_timeout) # not nice (should poll connection until success instead)
        logger.debug("using osm2pgsql binary %s" % osm2pgsql)
        osm2pgsql_proc = pexpect.spawn(string.join([osm2pgsql, "--create", "--database", db_name, "--cache", str(cache_size), "--number-processes", str(osm2pgsql_number_processes), "--slim", "--port", str(db_port), "--host", db_host, "--username", db_user, "--latlong", "--password", "--keep-coastlines", "--extra-attributes", "--hstore-all"]+osm_files, " "))
        osm2pgsql_proc.logfile = sys.stdout
        osm2pgsql_proc.expect(['Password:', "Passwort:"])
        osm2pgsql_proc.sendline(db_password)
        osm2pgsql_proc.timeout = 100000000
        osm2pgsql_proc.expect(pexpect.EOF)
    except Exception as ex:
        logger.error(ex)
    finally:
        if not postgres_proc is None:
            postgres_proc.terminate() # there's no check for subprocess.Popen 
                    # whether it is alive, subprocess.Popen.terminate can be 
                    # invoked without risk on a terminated process

if __name__ == "__main__":
    args = vars(parser.parse_args())
    data_dir = args[data_dir_option_long]
    osm2pgsql = args[osm2pgsql_option_long]
    osm_postgis_transform(data_dir = data_dir, osm_files=args[osm_files_option_long], cache_size=args[cache_size_option_long], db_user=args[db_user_option_long], db_password=args[db_password_option_long], db_host=args[db_host_option_long], db_port=args[db_port_option_long], db_name=args[db_name_option_long], start_db=args[start_db_option_long], osm2pgsql=osm2pgsql)

