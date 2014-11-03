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

# python-provided dependencies
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
import shutil

# project internal dependencies
sys.path.append(os.path.realpath(os.path.join(__file__, "..", 'lib')))
import pm_utils
import check_os
import postgis_utils
import os_utils

# external dependencies
try:
    import pexpect
    import plac
except ImportError as ex:
    logger.error("import of one of the modules %s failed. Did you run the osm_postgis_transform_prequisites.py scripts?" % ["pexpect", "plac"])

pg_version = (9,2)
pg_version_string = str.join(".", [str(i) for i in pg_version])
postgis_version = (2,0)
postgis_version_string = str.join(".", [str(i) for i in postgis_version])
initdb = "/usr/lib/postgresql/%s/bin/initdb" % pg_version_string
postgres = "/usr/lib/postgresql/%s/bin/postgres" % pg_version_string
psql = "/usr/lib/postgresql/%s/bin/psql" % pg_version_string
createdb = "/usr/lib/postgresql/%s/bin/createdb" % pg_version_string
osm2pgsql_number_processes = int(sp.check_output(["grep", "-c", "^processor", "/proc/cpuinfo"]).strip())
db_socket_dir = "/tmp"

start_db_default = False
db_host_default = "localhost"
db_port_default = 5204
db_user_default = "postgis"
db_password_default = "postgis"
db_name_default = "postgis"
osm2pgsql_default = "osm2pgsql"
data_dir_default = os.path.join(os.environ["HOME"], "osm_postgis/postgis-%s" % pg_version_string)
cache_size_default=1000

# the time the scripts (main thread) waits for the postgres server to be available and accepting connections (in seconds)
postgres_server_start_timeout = 5

def a_list(arg):
    return arg.split(",")

# fails by default because osm_files mustn't be empty
# @args db_user when <tt>start_db</tt> is <code>True</code> used as superuser name, otherwise user to connect as to the database denotes by <tt>db_*</tt> parameter of this function
@plac.annotations(
    osm_files=("a comma (`,`) separated list of OSM files to be passed to osm2pgsql (gunzipped files are accepted if osm2pgsql accepts them (the version installed by osm_postgis_transform_prequisites does))", "positional", None, a_list), 
    skip_start_db=("Specify this flag in order to feed the data to an already running postgres process which the script will attempt to connect to with the parameters specified by `db-host`, `db-port`, `db-user`, `db-password` and `db-name` arguments.", "flag"),     
    data_dir=("The directory which contains or will contain the data of the PostGIS database (see documentation of `-D` option in `man initdb` for further details). The directory will be created if it doesn't exist. If a file is passed as argument, the script will fail argument validation. The script will fail if the directory is an invalid PostGIS data directory (e.g. one which allows partial start of a `postgres` process but contains invalid permissions or misses files). As soon as a non-empty directory is passed as argument, it is expected to be a valid PostGIS data directory! If the script fails due to an unexpected error, YOU have to take care of cleaning that directory from anything besides the stuff inside before the script has been invoked!", "option"), 
    db_host=("The host where the nested database process should run (has to be specified if default value isn't reachable) or the host where to reach the already running postgres process (see --start-db for details)", "option"), 
    db_port=("The port where the nested database process will be listening (has to be specified if the port denoted by the default value is occupied) or the port where to reach the already running postgres process (see --start-db for details)", "option"), 
    db_user=("name of user to use for authentication at the database (will be created if database doesn't exist) (see --start-db for details)", "option"), 
    db_password=("password for the user specified with `--db-user` argument to use for authentication at the database (will be set up if database doesn't exist) (see --start-db for details)", "option"), 
    db_name=("name of the database to connect to or to be created (see --start-db for details)", "option"), 
    cache_size=("size of osm2pgsql cache (see `--cache` option of `man osm2pgsql`)", "option"), 
    osm2pgsql=("optional path to a osm2pgsql binary", "option"), 
)
def osm_postgis_transform(osm_files, skip_start_db, data_dir=data_dir_default, db_host=db_host_default, db_port=db_port_default, db_user=db_user_default, db_password=db_password_default, db_name=db_name_default, cache_size=cache_size_default, osm2pgsql=osm2pgsql_default):
    # the text for the help transformed by plac:
    """
    This script sets up PostGIS database with data from an OSM (.osm) file. It 
    is essentially a wrapper around `osm2pgsql`. By default it will either spawn a database process based on the data directory speified with the `--data-dir` argument (if the data directory is non-empty) or create a database data directory and spawn a database process based on that newly created data directory and feed data to it. If the nested database process can't be connected to with the default value for database connection parameters, they have to be overwritten, otherwise the script will fail with the error message of the `postgres` process.
    
    The start of a nested database process can be skipped if `--skip-start-db` command line flag is set. In this case the database connection parameters will be used to connect to an external already running `postgres` process where data will be fed to.
    
    WARNING: The script has not yet been tested completely to hide database credentials (including the password) from output and/or other logging backends (files, syslog, etc.). It is currently recommended to specify a separate database and local host for the script only and to not care about it at all (as OSM data is as far from a secret as it could be).
    """
    if osm_files is None:
        raise ValueError("osm_files mustn't be None")
    if str(type(osm_files)) != "<type 'list'>":
        raise ValueError("osm_files has to be a list")
    if len(osm_files) == 0:
        raise ValueError("osm_files mustn't be empty")
    if pg_version == (9,2):
        if postgis_version > (2,0):
            raise ValueError("postgis > %s is not compatible with postgresql %s" % (postgis_version_string, pg_version_string))
    if data_dir is None:
        raise ValueError("data_dir mustn't be None")
    if os.path.exists(data_dir) and not os.path.isdir(data_dir):
        raise ValueError("data_dir '%s' exists, but isn't a directory" % (data_dir,))
    
    # always check, even after install_prequisites
    #@TODO: not sufficient to binary name; necessary to evaluate absolute path with respect to $PATH
    if os_utils.which(osm2pgsql) is None:
        raise RuntimeError("osm2pgsql not found, make sure you have invoked osm_postgis_transform_prequisites.py")
    
    # parsing
    # postgres binary refuses to run when process uid and effective uid are not identical    
    postgres_proc = None
    try:
        if not skip_start_db:
            # database process is either started by postgis_utils.bootstrap_datadir or with pexpect.spawn if the data_dir isn't empty (indicating start of database based on existing data directory)
            if not os.path.exists(data_dir) or len(os.listdir(data_dir)) == 0:
                logger.info("creating PostGIS data directory in data_dir '%s'" % (data_dir,))
                if not os.path.exists(data_dir):
                    logger.info("creating inexisting data_dir '%s'" % (data_dir,))
                    os.makedirs(data_dir)
                postgis_utils.bootstrap_datadir(data_dir, db_user, password=db_password, initdb=initdb)
                postgis_utils.bootstrap_database(data_dir, db_port, db_host, db_user, db_name, password=db_password, initdb=initdb, postgres=postgres, createdb=createdb, psql=psql, socket_dir=db_socket_dir)
            if postgres_proc is None:
                logger.info("spawning database process based on existing data directory '%s'" % (data_dir,))
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
# internal implementation notes:
# - it would be nicer to validate the data directory rather than simply expect 
# it to be valid if it is non-empty

if __name__ == "__main__":
    plac.call(osm_postgis_transform)

