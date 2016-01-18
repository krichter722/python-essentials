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

# This file contains code which is used in different python-essentials scripts

# external dependencies
import os
import ConfigParser
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

config_file_name_default = "python-essentials.cfg"
config_file_pathes_default = [os.path.join(os.environ["HOME"], ".%s" % (config_file_name_default)), os.path.join("/etc", config_file_name_default), ]

# creates an instance of ConfigParser.ConfigParser which either has a file loaded or not. Retrieving values from it with ConfigParser.get should always be backed up by a default value.
# @args base_dir the directory against which the configuration file which is sibling of the invoked script
def create_config_parser(config_file_name=config_file_name_default, config_file_pathes=config_file_pathes_default):
    chosen_config_file_path = None
    for config_file_path in config_file_pathes:
        if os.path.exists(config_file_path):
            logger.info("using '%s' as configuration file" % (config_file_path))
            chosen_config_file_path = config_file_path
            break
    config = ConfigParser.ConfigParser()
    if chosen_config_file_path is None:
        logger.info("no configuration file found, using default values")
    else:
        # can't read None as argument passed to ConfigParser.read
        config.read(chosen_config_file_path)
    return config

