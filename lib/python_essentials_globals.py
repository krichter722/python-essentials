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

# The file provides programmatic default values as python constants. It isn't 
# necessary to read the values from a config file which is maintained in the 
# sources tree, but this way we have a default config file without any further 
# efforts

import os
import check_os

app_name = "python_essentials"
app_version = (1, 1, 4)
app_version_string = str.join(".", [str(x) for x in app_version])

if check_os.check_python3():
    import configparser
    config = configparser.ConfigParser()
else:
    import ConfigParser
    config = ConfigParser.ConfigParser()
defaults_config_file_path = os.path.join(os.path.realpath(__file__), "..", "python-essentials.cfg")
config.read(defaults_config_file_path)
osm_postgis_dir_path = os.path.join(os.environ["HOME"], "osm_postgis_db-9.2") # config.get("pathes", "osm_postgis_dir_path")
osm_postgis_version = (9,2) # config.get("versions", "osm_postgis_version")

